#!/usr/bin/env python3
"""Add the QA internal-traffic flag (`?am_internal=1`) to every page's direct
GA4 gtag loader. Modelled on Tools/add-theme-support.py and
Tools/add-exam-page-cta.py: a single (anchor, replacement) edit, asserted to
match exactly once per file before anything is written; a file that already
carries the complete generated block is validated so re-runs are no-ops.

Why: GA4 (measurement ID G-YTN7LFS04Y, loaded directly via gtag — there is no
GTM on these pages) currently counts the owner's own QA visits. A one-time
`?am_internal=1` visit sets a same-origin localStorage marker; every gtag
config call thereafter (this visit and all future ones) sends
`traffic_type: 'internal'` first, which GA4's Internal Traffic filter uses to
drop the events. No cookies — see Tools/PERFORMANCE.md's "one GA loader per
page" rule, which this script does not touch (it edits the existing inline
config block, it never adds a loader).

Targets are discovered dynamically: every *.html file found by walking the
site root (`Path(SITE).rglob("*.html")`, skipping any path with a
`.worktrees`, `.git`, `.superpowers` or `node_modules` segment) whose text
contains the direct gtag loader (`gtag/js?id=G-YTN7LFS04Y`). Walking the
filesystem directly rather than shelling out to `grep -rl` means the result
does not depend on which `grep` is on PATH (BSD vs. GNU flag differences)
and cannot wander into a sibling worktree sharing this checkout's disk. In
this repo that is every homepage/exam-page/guide/hub file plus
exams/_template.html — all 47 of them share byte-identical indentation for
the five-line config block (2-space script tags, 4-space body), verified
before this tool was written, so a single anchor covers every one. 404.html
and the three apps/AzureMastery/{support,privacy,terms}.html legal pages do
NOT carry this block at all — they either have no analytics (404.html) or
run GTM (GTM-TK79R26R) instead of direct gtag — so they are silently absent
from the target list rather than skipped-with-a-marker; run with no
arguments to see the full target list printed.

    python3 Tools/add-ga-internal-flag.py            # apply
    python3 Tools/add-ga-internal-flag.py --check    # dry run; report only, exit 1 on drift
"""
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv[1:]

MARKER = "am_internal"
GTAG_LOADER = "gtag/js?id=G-YTN7LFS04Y"
SKIP_SEGMENTS = {".worktrees", ".git", ".superpowers", "node_modules"}

ANCHOR = (
    "  <script>\n"
    "    window.dataLayer = window.dataLayer || [];\n"
    "    function gtag(){dataLayer.push(arguments);}\n"
    "    gtag('js', new Date());\n"
    "    gtag('config', 'G-YTN7LFS04Y');\n"
    "  </script>"
)

REPLACEMENT = (
    "  <script>\n"
    "    window.dataLayer = window.dataLayer || [];\n"
    "    function gtag(){dataLayer.push(arguments);}\n"
    "    gtag('js', new Date());\n"
    "    // QA browsers opt themselves out of reporting once via ?am_internal=1. The flag is a\n"
    "    // self-set localStorage marker on this origin only; GA4's Internal Traffic filter\n"
    "    // drops events that carry traffic_type=internal.\n"
    "    try {\n"
    "      if (/[?&]am_internal=1(&|$)/.test(location.search)) localStorage.setItem('am_internal', '1');\n"
    "      if (localStorage.getItem('am_internal') === '1') gtag('set', { traffic_type: 'internal' });\n"
    "    } catch (e) {}\n"
    "    gtag('config', 'G-YTN7LFS04Y');\n"
    "  </script>"
)


def find_targets() -> list[Path]:
    paths = []
    for path in SITE.rglob("*.html"):
        rel = path.relative_to(SITE)
        if SKIP_SEGMENTS & set(rel.parts[:-1]):
            continue
        if GTAG_LOADER in path.read_text():
            paths.append(path)
    return sorted(paths)


def process(path: Path) -> str:
    text = path.read_text()
    replacement_count = text.count(REPLACEMENT)
    if replacement_count:
        if replacement_count != 1:
            raise AssertionError(
                f"{path}: complete internal-traffic block matched "
                f"{replacement_count} times (want 1)"
            )
        return "skip (already flagged)"
    if MARKER in text:
        raise AssertionError(
            f"{path}: found the {MARKER!r} marker without the complete internal-traffic block"
        )
    count = text.count(ANCHOR)
    if count != 1:
        raise AssertionError(f"{path}: anchor matched {count} times (want 1)")
    new_text = text.replace(ANCHOR, REPLACEMENT, 1)
    if new_text.count(REPLACEMENT) != 1:
        raise AssertionError(
            f"{path}: generated internal-traffic block is not present exactly once"
        )
    if not CHECK:
        path.write_text(new_text)
    return "updated" if not CHECK else "would update"


def main() -> int:
    targets = find_targets()
    if not targets:
        print("no targets found (gtag/js?id=G-YTN7LFS04Y not present anywhere)", file=sys.stderr)
        return 1

    results: list[tuple[str, str]] = []
    failures: list[str] = []
    for path in targets:
        label = str(path.relative_to(SITE))
        try:
            results.append((label, process(path)))
        except AssertionError as exc:
            failures.append(str(exc))
            results.append((label, "FAILED"))

    width = max(len(label) for label, _ in results)
    for label, status in results:
        print(f"{label:{width}s}  {status}")

    changed = sum(1 for _, status in results if status.startswith("updated") or status.startswith("would update"))
    print(f"\n{len(results)} file(s) checked, {changed} changed, {len(failures)} failure(s)")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    if CHECK and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
