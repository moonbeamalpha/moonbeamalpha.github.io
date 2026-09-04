#!/usr/bin/env python3
"""Ratchet against the exam pages reading as one templated skeleton.

Google demoted azuremastery.app on 2026-07-29 with nothing flagged in Search
Console; the leading suspect is that the exam pages share one skeleton, one
set of mock-ups and mostly the same "how the app helps" prose, with only
objectives and study plans differing per exam (see the Track B / task-B3
brief). Task B3b rewrites #objectives, adds a "Where candidates slip" section
and rewrites FAQs/how-helps prose per exam, page by page. This tool measures
whether that's actually working: it compares every pair of exam pages' visible
body text and flags pairs that still read as near-duplicates, plus tracks the
corpus-wide mean, as a ratchet that only ever tightens.

Scope: CURRENT exam pages only -- a page whose code is not in
data/exam-counts.json's "retired" list (today AI-102, AI-900, AZ-204, AZ-500,
DP-100; Tools/sync-marketing-counts.py owns that classification, this tool
only reads it). A retired page's copy is deliberately generic ("this exam has
retired, here's its successor") rather than de-templated content, so mixing
it into the corpus would understate how similar the current pages actually
are -- exactly what this ratchet exists to catch. That leaves 30 pages / 435
pairs as of Sep 2026. exams/index.html (the pages hub) and
exams/retired/index.html (the retired-exams hub) are excluded too -- neither
is an exam page at all.

Method: each page's <body> is reduced to a word list (tags stripped, comments
and non-visible chrome removed -- see extract_words()), and every unordered
pair is compared with difflib.SequenceMatcher(None, words_a, words_b).ratio().
Word lists, not raw character text or a 5-word shingle Jaccard: SequenceMatcher
on words is what the brief asks for by default, and it comfortably profiles at
well under a second for all 435 pairs on this corpus (Sep 2026 measurement) --
fast enough that the shingle-Jaccard fallback was never needed.

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
  python3 Tools/check-page-similarity.py --drop AB-100     # debug: exclude a code from
                                                            # the current corpus, to rehearse
                                                            # what --check does when a page
                                                            # retires (repeatable)

Baseline file: Tools/page-similarity-baseline.json =
  {"max_pair": <float>, "mean": <float>, "pages": [<code>, ...], "pairs": {"A~B": <float>, ...}}
-- every pair among the pages current when --update-baseline last ran, 6 decimal
places, dict keys sorted (json.dump(..., sort_keys=True) does this for free
since "A~B" sorts lexically the same way the pages do).

--check is immune to corpus-membership changes (a page retiring or a new exam
page landing) by construction, not by exempting anything from scrutiny:

  (i)   For every pair present in BOTH the baseline and the current corpus --
        i.e. both of its pages are still current -- the drift check compares
        like with like: this pair's CURRENT ratio against its own BASELINE
        ratio with the existing +0.005 tolerance. Shared-pairs mean and max
        summaries are checked too, so both local cloning and broad corpus
        convergence fail the ratchet. A page retiring changes which
        pairs are "shared" but never changes what a still-current pair's own
        historical ratio was, so removing a page cannot move this number the
        way comparing against the old whole-corpus mean/max could.
  (ii)  Any pair involving a page NOT in the baseline (a brand new exam page)
        has no historical ratio to diff against, so it is held to an absolute
        bar instead: its ratio must be <= the baseline's overall max_pair +
        tolerance, or --check fails with "new page <code> pairs above the
        ratchet -- de-template it". This is exactly as strict as the ratchet
        already is for every existing page's pairs.
  (iii) A page that left the corpus (retired) simply has no current pairs at
        all -- neither (i) nor (ii) has anything to say about it, so it can
        never fail. Confirmed by rehearsal: `--drop AB-100` still passes
        --check against the committed baseline (see the task-B brief).

Pages added/removed relative to the baseline are printed either way, so a
clean --check run still shows corpus churn even though it can't fail on it.
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
DATA_FILE = os.path.join(ROOT, "data", "exam-counts.json")
BASELINE_FILE = os.path.join(ROOT, "Tools", "page-similarity-baseline.json")

# An exam page's directory looks like "az-104" -- this both excludes the two
# hub pages (exams/index.html, exams/retired/index.html) that the one-level
# glob would otherwise pick up and doubles as a sanity check on every
# directory this tool treats as an exam page.
CODE_DIR_RE = re.compile(r'^[a-z]{2}-\d{3}$')

# Pairs at or below this ratio aren't printed in the report -- with 30
# heavily templated current pages today, nearly every pair clears it, which
# is itself the finding this tool exists to surface. As B3b diverges pages,
# the printed list should shrink.
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


def load_retired_codes() -> set[str]:
    """Uppercase codes data/exam-counts.json lists as non-current (any exam
    carrying a Microsoft retirement date, e.g. AI-102). This is the same
    classification Tools/sync-marketing-counts.py's non_current_exams() uses
    -- that tool owns it, this one only reads the committed snapshot."""
    if not os.path.exists(DATA_FILE):
        sys.exit(f"error: {os.path.relpath(DATA_FILE, ROOT)} missing — "
                 f"run sync-marketing-counts.py --refresh first.")
    with open(DATA_FILE) as fh:
        data = json.load(fh)
    return set(data.get("retired") or ())


def exam_pages(retired: set[str], drop: set[str] = frozenset()) -> list[str]:
    """Every CURRENT exams/<code>/index.html, sorted. "Current" excludes:
    - exams/index.html and exams/retired/index.html -- neither directory
      name matches CODE_DIR_RE, so both hub pages drop out without a
      special case;
    - any exams/<code>/index.html whose code is in `retired` -- a retired
      exam's page is deliberately generic ("this exam has retired, here's
      its successor"), so including it would understate how similar the
      current pages are to each other;
    - any code in `drop` -- the --drop debug flag, for rehearsing what
      --check does when a page leaves the corpus without editing
      data/exam-counts.json."""
    pages = []
    for path in sorted(glob.glob(os.path.join(EXAMS_DIR, "*", "index.html"))):
        code_dir = os.path.basename(os.path.dirname(path))
        if not CODE_DIR_RE.match(code_dir):
            continue
        if code_dir.upper() in retired or code_dir.upper() in drop:
            continue
        pages.append(path)
    return pages


def page_code(path: str) -> str:
    return os.path.basename(os.path.dirname(path)).upper()


def pair_key(a: str, b: str) -> str:
    """Canonical, order-independent key for a pair of codes."""
    lo, hi = sorted((a, b))
    return f"{lo}~{hi}"


def compute_pairs(drop: set[str] = frozenset()) -> tuple[list[str], dict[str, float]]:
    """Returns (sorted current codes, {pair_key: ratio} for every pair)."""
    pages = exam_pages(load_retired_codes(), drop)
    if len(pages) < 2:
        sys.exit(f"error: found {len(pages)} current exam page(s) under {EXAMS_DIR} — need at least 2.")
    words = {p: extract_words(p) for p in pages}
    codes = sorted(page_code(p) for p in pages)
    pairs: dict[str, float] = {}
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            a, b = pages[i], pages[j]
            ratio = difflib.SequenceMatcher(None, words[a], words[b]).ratio()
            pairs[pair_key(page_code(a), page_code(b))] = ratio
    return codes, pairs


def summarise(pairs: dict[str, float]) -> tuple[float, float]:
    """(max_pair, mean) over the given pair-ratio mapping."""
    values = list(pairs.values())
    return max(values), statistics.mean(values)


def as_sorted_list(pairs: dict[str, float]) -> list[tuple[float, str, str]]:
    """{pair_key: ratio} -> [(ratio, code_a, code_b), ...] sorted descending,
    for the human-readable report."""
    out = []
    for key, ratio in pairs.items():
        a, b = key.split("~", 1)
        out.append((ratio, a, b))
    out.sort(key=lambda t: t[0], reverse=True)
    return out


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
        data = json.load(fh)
    # Tolerate the pre-W3a baseline shape (no "pages"/"pairs") so a fresh
    # checkout mid-migration fails with a clear instruction rather than a
    # KeyError.
    if "pages" not in data or "pairs" not in data:
        sys.exit(f"error: {os.path.relpath(BASELINE_FILE, ROOT)} is in the old "
                 f"shape (no pages/pairs) — run with --update-baseline first.")
    return data


def write_baseline(codes: list[str], pairs: dict[str, float], max_pair: float, mean: float) -> None:
    data = {
        "max_pair": round(max_pair, 6),
        "mean": round(mean, 6),
        "pages": sorted(codes),
        "pairs": {k: round(v, 6) for k, v in pairs.items()},
    }
    with open(BASELINE_FILE, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"wrote {os.path.relpath(BASELINE_FILE, ROOT)}: "
          f"{len(data['pages'])} pages, {len(data['pairs'])} pairs, "
          f"max_pair={data['max_pair']}, mean={data['mean']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the ratchet regressed (see the module docstring)")
    ap.add_argument("--update-baseline", action="store_true",
                    help="write the current pages/pairs/max_pair/mean as the new baseline")
    ap.add_argument("--drop", action="append", default=[], metavar="CODE",
                    help="debug: exclude CODE from the current corpus (repeatable) -- "
                         "for rehearsing what --check does when a page retires")
    args = ap.parse_args()
    if args.check and args.update_baseline:
        sys.exit("error: pass one of --check or --update-baseline, not both.")

    drop = {c.upper() for c in args.drop}
    codes, pairs = compute_pairs(drop)
    max_pair, mean = summarise(pairs)
    print_report(as_sorted_list(pairs), mean)

    if args.update_baseline:
        write_baseline(codes, pairs, max_pair, mean)
        return

    if args.check:
        baseline = load_baseline()
        base_pages = set(baseline["pages"])
        base_pairs: dict[str, float] = baseline["pairs"]
        base_max = baseline["max_pair"]

        current_codes = set(codes)
        added = sorted(current_codes - base_pages)
        removed = sorted(base_pages - current_codes)
        if added:
            print(f"pages added since baseline: {', '.join(added)}")
        if removed:
            print(f"pages removed since baseline (e.g. retired): {', '.join(removed)}")
        if not added and not removed:
            print("no corpus membership changes since baseline")

        failed = False

        # (i) Pairs whose both pages are still current: compare this pair's
        # own baseline ratio against its own current ratio. Keep the aggregate
        # shared-only mean/max checks as broad-corpus signals, but do not rely
        # on them: one cloned pair can otherwise be diluted across 435 pairs
        # while remaining below whichever unrelated pair owns the maximum.
        shared_keys = base_pairs.keys() & pairs.keys()
        if shared_keys:
            pair_regressions = []
            for key in sorted(shared_keys):
                drift = pairs[key] - base_pairs[key]
                if drift > DRIFT_TOLERANCE:
                    pair_regressions.append((key, base_pairs[key], pairs[key], drift))
            for key, baseline_ratio, current_ratio, drift in pair_regressions:
                a, b = key.split("~", 1)
                print(f"  DRIFT  shared pair {a} ~ {b}: "
                      f"{baseline_ratio:.4f} -> {current_ratio:.4f} ({drift:+.4f})")
            if pair_regressions:
                print(f"FAIL  {len(pair_regressions)} shared pair(s) regressed above "
                      f"the +{DRIFT_TOLERANCE} tolerance.")
                failed = True

            shared_base_max, shared_base_mean = summarise({k: base_pairs[k] for k in shared_keys})
            shared_cur_max, shared_cur_mean = summarise({k: pairs[k] for k in shared_keys})
            max_drift = shared_cur_max - shared_base_max
            mean_drift = shared_cur_mean - shared_base_mean
            print(f"\nshared pairs: {len(shared_keys)} "
                  f"(tolerance +{DRIFT_TOLERANCE})")
            print(f"  baseline: max_pair={shared_base_max:.4f} mean={shared_base_mean:.4f}")
            print(f"  current:  max_pair={shared_cur_max:.4f} ({max_drift:+.4f})  "
                  f"mean={shared_cur_mean:.4f} ({mean_drift:+.4f})")
            if max_drift > DRIFT_TOLERANCE or mean_drift > DRIFT_TOLERANCE:
                print("FAIL  similarity ratchet regressed on shared pairs — "
                      "pages have converged, not diverged.")
                failed = True
        else:
            print("\nno pairs shared with the baseline — nothing to diff.")

        # (ii) Pairs involving a page not in the baseline (a brand new exam
        # page) have no historical ratio to diff against, so hold them to an
        # absolute bar instead: no worse than the baseline's own overall
        # ceiling, plus the same tolerance.
        new_keys = pairs.keys() - base_pairs.keys()
        new_pages_over = set()
        for key in sorted(new_keys):
            if pairs[key] > base_max + DRIFT_TOLERANCE:
                a, b = key.split("~", 1)
                new_pages_over.update(c for c in (a, b) if c not in base_pages)
                print(f"  DRIFT  new pair {a} ~ {b} = {pairs[key]:.4f} "
                      f"> baseline max_pair {base_max:.4f} (+{DRIFT_TOLERANCE})")
        for code in sorted(new_pages_over):
            print(f"FAIL  new page {code} pairs above the ratchet — de-template it.")
            failed = True

        # (iii) Pages that left the corpus: their pairs are simply absent
        # from `pairs` entirely, so they never reach either check above.

        if failed:
            sys.exit(1)
        print("PASS  similarity ratchet holds.")


if __name__ == "__main__":
    main()
