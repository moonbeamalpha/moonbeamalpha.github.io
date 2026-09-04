#!/usr/bin/env python3
"""Ratchet against the exam pages reading as one templated skeleton.

Google demoted azuremastery.app on 2026-07-29 with nothing flagged in Search
Console; the leading suspect is that the 35 exam pages share one skeleton, one
set of mock-ups and mostly the same "how the app helps" prose, with only
objectives and study plans differing per exam (see the Track B / task-B3
brief). Task B3b rewrites #objectives, adds a "Where candidates slip" section
and rewrites FAQs/how-helps prose per exam, page by page. This tool measures
whether that's actually working: it compares every pair of exam pages' visible
body text and flags pairs that still read as near-duplicates, plus tracks the
corpus-wide mean, as a ratchet that only ever tightens.

Method: each page's <body> is reduced to a word list (tags stripped, comments
and non-visible chrome removed -- see extract_words()), and every unordered
pair is compared with difflib.SequenceMatcher(None, words_a, words_b).ratio().
Word lists, not raw character text or a 5-word shingle Jaccard: SequenceMatcher
on words is what the brief asks for by default, and it comfortably profiles at
under 4 seconds for all C(35,2)=595 pairs on this corpus (Sep 2026 measurement)
-- fast enough that the shingle-Jaccard fallback was never needed.

Excluded before comparison (the brief's list -- shared or duplicated-by-design
markup that would otherwise inflate every pair equally and hide genuine
content overlap): <header>, <footer>, <nav class="page-toc">, the
<div class="question-types"> block (six tool-generated mock-ups, byte-identical
in shape across every page by design -- B3b is expressly forbidden from
touching them), and <script>/<style> blocks.

Usage:
  python3 Tools/check-page-similarity.py                  # report: top pairs + mean
  python3 Tools/check-page-similarity.py --check           # exit 1 if the ratchet slipped
  python3 Tools/check-page-similarity.py --update-baseline # write the new baseline

Baseline file: Tools/page-similarity-baseline.json = {"max_pair": <float>, "mean": <float>}.
--check fails when either the highest pair or the corpus mean grows by more
than 0.005 over the committed baseline -- rewriting a page can only lower
similarity against its siblings, never (deliberately) raise it, so the
baseline should only ever tighten via --update-baseline after a page lands.
"""

from __future__ import annotations

import argparse
import difflib
import glob
import html
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMS_DIR = os.path.join(ROOT, "exams")
BASELINE_FILE = os.path.join(ROOT, "Tools", "page-similarity-baseline.json")

# Pairs at or below this ratio aren't printed in the report -- with 35 heavily
# templated pages today, nearly every pair clears it, which is itself the
# finding this tool exists to surface. As B3b diverges pages, the printed list
# should shrink.
REPORT_THRESHOLD = 0.30
# --check tolerance: how much either summary number may grow over the
# committed baseline before this is treated as a regression.
DRIFT_TOLERANCE = 0.005

_SCRIPT_STYLE_RE = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.I | re.S)
_HEADER_RE = re.compile(r'<header\b[^>]*>.*?</header>', re.I | re.S)
_FOOTER_RE = re.compile(r'<footer\b[^>]*>.*?</footer>', re.I | re.S)
_PAGE_TOC_RE = re.compile(r'<nav\s+class="page-toc"[^>]*>.*?</nav>', re.I | re.S)
_QUESTION_TYPES_OPEN_RE = re.compile(r'<div\s+class="question-types"[^>]*>', re.I)
_DIV_TAG_RE = re.compile(r'<div\b|</div>', re.I)
_TAG_RE = re.compile(r'<[^>]+>')
_WORD_RE = re.compile(r"[a-z0-9']+")


def _strip_question_types(text: str) -> str:
    """Remove every <div class="question-types" ...>...</div> block, matching
    the closing tag by depth-counting nested <div>s rather than a naive
    non-greedy regex -- the block contains its own nested .qt__viz divs, so a
    lazy `.*?</div>` would close on the first one and leave most of the mock-up
    markup in the comparison text."""
    out = []
    pos = 0
    while True:
        m = _QUESTION_TYPES_OPEN_RE.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        out.append(text[pos:m.start()])
        depth = 1
        end = None
        for tm in _DIV_TAG_RE.finditer(text, m.end()):
            if tm.group(0).lower() == '</div>':
                depth -= 1
                if depth == 0:
                    end = tm.end()
                    break
            else:
                depth += 1
        if end is None:
            # Malformed/unbalanced markup -- bail out rather than risk eating
            # the rest of the page; leave everything from the open tag onward.
            out.append(text[m.start():])
            pos = len(text)
            break
        pos = end
    return ''.join(out)


def extract_words(path: str) -> list[str]:
    """Visible body text of an exam page, reduced to a lowercase word list."""
    text = open(path, encoding="utf-8").read()
    text = _SCRIPT_STYLE_RE.sub(' ', text)
    text = _HEADER_RE.sub(' ', text)
    text = _FOOTER_RE.sub(' ', text)
    text = _PAGE_TOC_RE.sub(' ', text)
    text = _strip_question_types(text)
    text = _TAG_RE.sub(' ', text)
    text = html.unescape(text)
    return _WORD_RE.findall(text.lower())


def exam_pages() -> list[str]:
    """Every exams/<code>/index.html, sorted. exams/index.html itself (the
    hub) is one directory shallower, so the one-level glob excludes it without
    a special case."""
    return sorted(glob.glob(os.path.join(EXAMS_DIR, "*", "index.html")))


def page_code(path: str) -> str:
    return os.path.basename(os.path.dirname(path)).upper()


def compute_pairs() -> tuple[list[tuple[float, str, str]], float]:
    """Returns (pairs sorted by ratio descending, corpus mean). Each pair is
    (ratio, code_a, code_b)."""
    pages = exam_pages()
    if len(pages) < 2:
        sys.exit(f"error: found {len(pages)} exam page(s) under {EXAMS_DIR} — need at least 2.")
    words = {p: extract_words(p) for p in pages}
    pairs = []
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            a, b = pages[i], pages[j]
            ratio = difflib.SequenceMatcher(None, words[a], words[b]).ratio()
            pairs.append((ratio, page_code(a), page_code(b)))
    pairs.sort(key=lambda t: t[0], reverse=True)
    mean = statistics.mean(r for r, _, _ in pairs)
    return pairs, mean


def print_report(pairs: list[tuple[float, str, str]], mean: float) -> None:
    above = [pr for pr in pairs if pr[0] > REPORT_THRESHOLD]
    print(f"{len(pairs)} page pair(s) compared, {len(above)} above {REPORT_THRESHOLD:.2f}:")
    for ratio, a, b in above:
        print(f"  {ratio:.4f}  {a} ~ {b}")
    print(f"mean similarity: {mean:.4f}")
    if pairs:
        print(f"highest pair: {pairs[0][0]:.4f}  {pairs[0][1]} ~ {pairs[0][2]}")


def load_baseline() -> dict:
    if not os.path.exists(BASELINE_FILE):
        sys.exit(f"error: {os.path.relpath(BASELINE_FILE, ROOT)} missing — "
                 f"run with --update-baseline first.")
    with open(BASELINE_FILE) as fh:
        return json.load(fh)


def write_baseline(max_pair: float, mean: float) -> None:
    data = {"max_pair": round(max_pair, 6), "mean": round(mean, 6)}
    with open(BASELINE_FILE, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"wrote {os.path.relpath(BASELINE_FILE, ROOT)}: {data}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if max_pair or mean grew more than the tolerance over the baseline")
    ap.add_argument("--update-baseline", action="store_true",
                    help="write the current max_pair/mean as the new baseline")
    args = ap.parse_args()
    if args.check and args.update_baseline:
        sys.exit("error: pass one of --check or --update-baseline, not both.")

    pairs, mean = compute_pairs()
    max_pair = pairs[0][0] if pairs else 0.0
    print_report(pairs, mean)

    if args.update_baseline:
        write_baseline(max_pair, mean)
        return

    if args.check:
        baseline = load_baseline()
        base_max = baseline["max_pair"]
        base_mean = baseline["mean"]
        max_drift = max_pair - base_max
        mean_drift = mean - base_mean
        print(f"\nbaseline: max_pair={base_max:.4f} mean={base_mean:.4f} "
              f"(tolerance +{DRIFT_TOLERANCE})")
        print(f"current:  max_pair={max_pair:.4f} ({max_drift:+.4f})  "
              f"mean={mean:.4f} ({mean_drift:+.4f})")
        if max_drift > DRIFT_TOLERANCE or mean_drift > DRIFT_TOLERANCE:
            print("FAIL  similarity ratchet regressed — pages have converged, not diverged.")
            sys.exit(1)
        print("PASS  similarity ratchet holds.")


if __name__ == "__main__":
    main()
