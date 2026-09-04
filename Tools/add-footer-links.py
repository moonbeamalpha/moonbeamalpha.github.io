#!/usr/bin/env python3
"""Add /about/ and /how-we-write-questions/ links to the footer link row on
every static page. Modelled on Tools/add-theme-support.py: a fixed anchor is
asserted to match 0-or-1 times per file before anything is written, and a
file that already carries the About link is skipped outright so re-runs are
no-ops.

Targets mirror Tools/sync-social-footer.py's target_pages() (duplicated here
rather than imported, since that module's hyphenated filename isn't a valid
Python import name — keep the two lists in sync by hand if either changes).

Two footer-row shapes exist on the site, so there are two anchors:

  - The homepage's <nav class="footer-links"> list (one link per line, no
    separator): anchored on the relative-href Support link,
    `<a href="apps/AzureMastery/support.html">Support</a>`.
  - Every exam page, guide page, and the three trust pages themselves use a
    dot-separated <p> footer (` · ` between links, absolute hrefs): anchored
    on `<a href="/apps/AzureMastery/support.html">Support</a> ·`.

apps/AzureMastery/{privacy,terms,support}.html are deliberately NOT patched:
they use a third, unrelated footer-nav pattern (self-referential — support.html
has no "Support" link to itself) with no comparable anchor to insert before,
so a page landing in neither list above is reported as skipped rather than
failing the assertion.

    python3 Tools/add-footer-links.py            # apply
    python3 Tools/add-footer-links.py --check    # dry run; report only, exit 1 on drift
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv[1:]

# Matches the inserted About link even if a later pass (e.g. aria-current="page"
# on the trust pages' own footer self-link) adds attributes to it — the
# inserted literal itself never changes.
MARKER_RE = re.compile(r'<a href="/about/"[^>]*>About</a>')

# (anchor, indent) pairs, tried in order. The inserted lines are built from
# `indent` and carry the same trailing separator style as the anchor itself.
NAV_LIST_ANCHOR = '<a href="apps/AzureMastery/support.html">Support</a>'
DOT_SEPARATED_ANCHOR = '<a href="/apps/AzureMastery/support.html">Support</a> ·'


def target_pages() -> list[Path]:
    pages = [ROOT / "index.html", ROOT / "404.html", ROOT / "exams" / "_template.html"]
    pages.extend(sorted((ROOT / "exams").glob("*/index.html")))
    pages.append(ROOT / "guides" / "index.html")
    pages.extend(sorted((ROOT / "guides").glob("*/index.html")))
    pages.extend(
        ROOT / slug / "index.html"
        for slug in ("about", "how-we-write-questions", "how-exam-iq-works")
    )
    pages.extend(
        ROOT / "apps" / "AzureMastery" / name
        for name in ("privacy.html", "terms.html", "support.html")
    )
    return pages


def process(path: Path) -> str:
    text = path.read_text()
    if MARKER_RE.search(text):
        return "skip (already linked)"

    for anchor, sep in ((NAV_LIST_ANCHOR, ""), (DOT_SEPARATED_ANCHOR, " ·")):
        count = text.count(anchor)
        if count == 0:
            continue
        if count > 1:
            raise AssertionError(f"{path}: anchor {anchor!r} matched {count} times (want 1)")
        # Match the indentation of the line the anchor sits on.
        line_start = text.rfind("\n", 0, text.index(anchor)) + 1
        indent = text[line_start:text.index(anchor)]
        insertion = (
            f'<a href="/about/">About</a>{sep}\n'
            f'{indent}<a href="/how-we-write-questions/">How we write questions</a>{sep}\n'
            f'{indent}'
        )
        new_text = text.replace(anchor, insertion + anchor, 1)
        if not CHECK:
            path.write_text(new_text)
        return "would update" if CHECK else "updated"

    return "skip (no support link in a known footer shape)"


def main() -> int:
    results: list[tuple[str, str]] = []
    failures: list[str] = []
    for path in target_pages():
        label = str(path.relative_to(ROOT))
        try:
            results.append((label, process(path)))
        except AssertionError as exc:
            failures.append(str(exc))
            results.append((label, "FAILED"))

    width = max(len(label) for label, _ in results)
    for label, status in results:
        print(f"{label:{width}s}  {status}")

    changed = sum(1 for _, status in results if status in ("updated", "would update"))
    print(f"\n{len(results)} file(s) checked, {changed} changed, {len(failures)} failure(s)")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    if CHECK and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
