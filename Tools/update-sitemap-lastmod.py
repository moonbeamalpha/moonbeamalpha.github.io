#!/usr/bin/env python3
"""Derive sitemap.xml <lastmod> values from git history.

Each <url> block's <lastmod> should reflect when the page it points to
actually changed, not a hand-picked date. This tool computes that date from
git and writes it into sitemap.xml (or, with --check, only reports drift).

For every <url> block:
  * a <loc> ending in "/" maps to "<path>/index.html"
    (https://azuremastery.app/ -> index.html);
  * a <loc> ending in ".html" maps to that file directly.

The lastmod for a file is:
  * today's date (UTC) if `git status --porcelain -- <file>` reports it
    modified or untracked;
  * otherwise the date of its most recent commit
    (`git log -1 --format=%cs -- <file>`);
  * if git has no history at all for a clean file (should not happen),
    today's date, with a warning printed to stderr.

`<lastmod>` is inserted right after `<loc>` when a block has none (this is
true of the support/privacy/terms entries today); otherwise the existing
value is replaced. Everything else in sitemap.xml -- structure, <loc>,
<priority>, <changefreq>, entry order, indentation -- is left byte-for-byte
untouched.

`expected_lastmod(path)` and `loc_to_path(loc)` are meant to be imported by
Tools/validate-marketing-seo.py so the validator checks against the same
computation this tool writes, rather than duplicating the logic.

Usage:
  python3 Tools/update-sitemap-lastmod.py           # write, print count changed
  python3 Tools/update-sitemap-lastmod.py --check   # exit 1 if any entry is stale
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


def _repo_root() -> Path:
    """Resolve the repo root via git rather than assuming this script's
    parent directory is the root.

    This runs from the sitemap's own directory (Tools/'s parent), so it
    works the same whether the script lives in a normal checkout or a
    linked worktree -- `git rev-parse --show-toplevel` always returns the
    checkout this file actually lives in.
    """
    here = Path(__file__).resolve().parent
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=here,
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(out.stdout.strip())


ROOT = _repo_root()
SITEMAP = ROOT / "sitemap.xml"

URL_BLOCK_RE = re.compile(r"<url>.*?</url>", re.S)
LOC_RE = re.compile(r"<loc>(.*?)</loc>")
LASTMOD_RE = re.compile(r"<lastmod>(.*?)</lastmod>")
INDENT_BEFORE_LOC_RE = re.compile(r"([ \t]*)<loc>")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return result.stdout


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def loc_to_path(loc: str) -> Path:
    """Map a sitemap <loc> URL to the on-disk page file it represents."""
    url_path = urlsplit(loc).path
    if url_path.endswith("/"):
        return ROOT / url_path.lstrip("/") / "index.html"
    return ROOT / url_path.lstrip("/")


def expected_lastmod(path: Path) -> str:
    """Compute the git-derived <lastmod> value for a page file.

    Today's UTC date if the file has uncommitted changes (modified or
    untracked, per `git status --porcelain`); otherwise the date of its
    most recent commit. Falls back to today with a printed warning if git
    has no history at all for the file.
    """
    status = _git("status", "--porcelain", "--", str(path))
    if status.strip():
        return _today()
    log = _git("log", "-1", "--format=%cs", "--", str(path)).strip()
    if not log:
        print(f"warning: no git history for {path}; falling back to today's date", file=sys.stderr)
        return _today()
    return log


def _rewrite_block(block: str) -> tuple[str, str | None, str | None, str | None]:
    """Return (new_block, loc, current_lastmod, expected_lastmod).

    loc is None (block unchanged) if the block has no <loc>.
    """
    loc_match = LOC_RE.search(block)
    if not loc_match:
        return block, None, None, None

    loc = loc_match.group(1)
    expected = expected_lastmod(loc_to_path(loc))

    lastmod_match = LASTMOD_RE.search(block)
    if lastmod_match:
        current = lastmod_match.group(1)
        new_block = (
            block[: lastmod_match.start()]
            + f"<lastmod>{expected}</lastmod>"
            + block[lastmod_match.end() :]
        )
    else:
        current = None
        indent_match = INDENT_BEFORE_LOC_RE.search(block)
        indent = indent_match.group(1) if indent_match else "    "
        insert_at = loc_match.end()
        new_block = (
            block[:insert_at]
            + f"\n{indent}<lastmod>{expected}</lastmod>"
            + block[insert_at:]
        )
    return new_block, loc, current, expected


def process(text: str) -> tuple[str, list[dict[str, str | None]]]:
    changes: list[dict[str, str | None]] = []

    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        new_block, loc, current, expected = _rewrite_block(block)
        if loc is not None and new_block != block:
            changes.append({"loc": loc, "current": current, "expected": expected})
        return new_block

    new_text = URL_BLOCK_RE.sub(repl, text)
    return new_text, changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--check", action="store_true",
        help="exit 1 and list stale entries instead of writing sitemap.xml",
    )
    args = parser.parse_args()

    before = SITEMAP.read_text()
    after, changes = process(before)

    if args.check:
        if changes:
            print(f"{len(changes)} sitemap lastmod value(s) are stale:")
            for change in changes:
                current = change["current"] or "(missing)"
                print(f"  {change['loc']}: {current} -> {change['expected']}")
            sys.exit(1)
        print("sitemap lastmod values are all up to date.")
        return

    if after != before:
        SITEMAP.write_text(after)
    noun = "entry" if len(changes) == 1 else "entries"
    print(f"updated {len(changes)} sitemap lastmod {noun}")


if __name__ == "__main__":
    main()
