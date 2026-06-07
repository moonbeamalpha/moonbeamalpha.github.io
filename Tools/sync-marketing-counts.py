#!/usr/bin/env python3
"""Sync marketing-site question/exam/path counts from the app's source of truth.

The Azure Mastery marketing site hard-codes per-exam question counts and a few
aggregate totals (total questions, exam count, certification-path count) in
~30 static HTML files, repeated ~10x per page across <title>, meta, OpenGraph,
Twitter, JSON-LD, body copy, hero stats and cross-referencing "related" cards.
Hand-maintaining those drifts badly (19/27 pages were stale when this was
written). This script makes the app the single source of truth.

Source of truth (the app repo, a sibling checkout):
  - per-exam question count = len(json["questions"]) for each
      App/AzureMastery/Resources/<code>-questions.json
  - certification-path count = number of `CertPathDefinition(` in
      App/AzureMastery/Data/CertPathRegistry.swift

A snapshot is committed to data/exam-counts.json so the marketing repo is
self-contained (re-runnable without the app checkout). Refresh it with --refresh.

Aggregates shown on the homepage follow the app's own marketing rule
(CertPathRegistry.totalQuestionCountLabel): round the total DOWN to the nearest
500 and append "+".  e.g. 10,139 -> "10,000+".  The animated metric counter
parses leading digits only (regex ^(\\d+)(.*)), so commas would break it — the
metric stays comma-less ("10000") while prose uses the formatted "10,000+".

Usage:
  python3 Tools/sync-marketing-counts.py --refresh   # re-read app repo -> data file
  python3 Tools/sync-marketing-counts.py             # patch HTML from data file
  python3 Tools/sync-marketing-counts.py --check      # report drift, change nothing

App repo location defaults to the sibling "../AZ-104 Mastery"; override with
env AZURE_MASTERY_APP_REPO.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "exam-counts.json")
EXAMS_DIR = os.path.join(ROOT, "exams")
INDEX_HTML = os.path.join(ROOT, "index.html")
LLMS_TXT = os.path.join(ROOT, "llms.txt")

DEFAULT_APP_REPO = os.environ.get(
    "AZURE_MASTERY_APP_REPO",
    os.path.join(os.path.dirname(ROOT), "AZ-104 Mastery"),
)

# Word forms for the homepage headline-accent ("Twenty-eight certifications.").
_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
_TEENS = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
          "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def number_word(n: int) -> str:
    """Capitalised English word for 0..99 (enough for exam counts)."""
    if n < 10:
        w = _ONES[n]
    elif n < 20:
        w = _TEENS[n - 10]
    elif n < 100:
        w = _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")
    else:
        return str(n)
    return w[0].upper() + w[1:]


# ── code helpers ──────────────────────────────────────────────────────────

def slug_to_code(slug: str) -> str:
    """az104 -> AZ-104 ; gh900 -> GH-900."""
    m = re.match(r"([a-z]+)(\d+)", slug)
    return f"{m.group(1).upper()}-{m.group(2)}"


def code_to_dir(code: str) -> str:
    """AZ-104 -> az-104 (the /exams/<dir>/ folder name)."""
    return code.lower()


# ── data file ─────────────────────────────────────────────────────────────

def refresh_from_app(app_repo: str) -> dict:
    res_dir = os.path.join(app_repo, "App", "AzureMastery", "Resources")
    if not os.path.isdir(res_dir):
        sys.exit(f"error: app Resources not found at {res_dir}\n"
                 f"set AZURE_MASTERY_APP_REPO to the AZ-104 Mastery checkout.")
    exams = {}
    for fn in sorted(os.listdir(res_dir)):
        m = re.match(r"([a-z]+\d+)-questions\.json$", fn)
        if not m:
            continue
        with open(os.path.join(res_dir, fn)) as fh:
            doc = json.load(fh)
        qs = doc["questions"] if isinstance(doc, dict) else doc
        exams[slug_to_code(m.group(1))] = len(qs)

    registry = os.path.join(app_repo, "App", "AzureMastery", "Data", "CertPathRegistry.swift")
    cert_paths = None
    if os.path.exists(registry):
        cert_paths = open(registry).read().count("CertPathDefinition(")

    data = {"exams": exams, "cert_path_count": cert_paths}
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"refreshed {DATA_FILE}: {len(exams)} exams, "
          f"{sum(exams.values())} questions, {cert_paths} cert paths")
    return data


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        sys.exit(f"error: {DATA_FILE} missing — run with --refresh first.")
    with open(DATA_FILE) as fh:
        return json.load(fh)


# ── patching ──────────────────────────────────────────────────────────────

class Patcher:
    def __init__(self, check_only: bool):
        self.check_only = check_only
        self.changed_files = 0
        self.total_edits = 0

    def apply(self, path: str, edits) -> None:
        """edits: list of (regex, replacement) applied in order."""
        if not os.path.exists(path):
            print(f"  skip (missing): {os.path.relpath(path, ROOT)}")
            return
        original = open(path).read()
        text = original
        n = 0
        for pattern, repl in edits:
            text, k = re.subn(pattern, repl, text)
            n += k
        rel = os.path.relpath(path, ROOT)
        if text != original:
            self.changed_files += 1
            self.total_edits += n
            if self.check_only:
                print(f"  DRIFT  {rel}: {n} replacement(s) would change content")
            else:
                with open(path, "w") as fh:
                    fh.write(text)
                print(f"  synced {rel}: {n} replacement(s)")


def exam_page_edits(code: str, count: int):
    """Anchored, value-agnostic edits for a single exam page."""
    c = str(count)
    return [
        # hero stat span
        (r'(am-cert-hero__stat-count">)\d+', r'\g<1>' + c),
        # "<n> AZ-900 practice questions" / "... cert-specific questions"
        (rf'\b\d+(\s+{re.escape(code)}\s+(?:practice|cert-specific)\s+questions)', c + r'\1'),
        # bare "<n> cert-specific questions" (own page only — related cards say "practice questions")
        (r'\b\d+(\s+cert-specific\s+questions)', c + r'\1'),
        # "with <n> AZ-900 practice" (meta/JSON-LD lead-ins without the word "questions" adjacent)
        (rf'\b\d+(\s+{re.escape(code)}\s+practice\b)', c + r'\1'),
    ]


def patch_related_cards(text: str, counts: dict) -> tuple[str, int]:
    """In each <a class="related-card" href="/exams/<dir>/"> ... </a> block,
    rewrite the bare "<n> practice questions" hint to the linked exam's count."""
    edits = 0

    def repl(m):
        nonlocal edits
        block = m.group(0)
        href = re.search(r'href="/exams/([a-z]+-\d+)/"', block)
        if not href:
            return block
        code = href.group(1).upper()
        if code not in counts:
            return block
        new_block, k = re.subn(r'\b\d+(\s+practice\s+questions)',
                               str(counts[code]) + r'\1', block)
        edits += k
        return new_block

    text = re.sub(r'<a class="related-card"[^>]*>.*?</a>', repl, text, flags=re.S)
    return text, edits


def homepage_edits(total_label: str, metric_total: str, exam_count: int, cert_paths: int):
    """Anchored aggregate edits for index.html. Each pattern is keyed off stable
    surrounding text so per-pillar roadmap counts ('5 exams') are never touched."""
    ec = str(exam_count)
    cp = str(cert_paths)
    return [
        # ── total questions (prose: "9,000 questions", "9,000 practice questions", "9,000 Questions") ──
        # Require a thousands-grouped number (>=1 comma-group) and a lookbehind so we never
        # start mid-number. This excludes exam codes ("AZ-204 practice questions") and bare
        # keyword commas ("exam prep, practice questions") — both must stay untouched.
        (r'(?<![\d,])\d{1,3}(?:,\d{3})+\+?(\s+(?:practice\s+)?[Qq]uestions)', total_label + r'\1'),
        # ── metric counters (anchored on the adjacent metric-label) ──
        (r'(class="metric-number[^"]*"[^>]*>)\d+\+?(</span>\s*<span class="metric-label">Questions)',
         r'\g<1>' + metric_total + r'\2'),
        (r'(class="metric-number[^"]*"[^>]*>)\d+(</span>\s*<span class="metric-label">Exams)',
         r'\g<1>' + ec + r'\2'),
        # ── exam count (each anchored to a stable phrase) ──
        (r'\|\s*\d+(\s+Exams</title>)', '| ' + ec + r'\1'),
        (r'\b\d+(\s+Microsoft\s+certification\s+exams)', ec + r'\1'),
        (r'across\s+\d+(\s+Microsoft\s+[Ee]xams)', 'across ' + ec + r'\1'),
        (r'across\s+\d+(\s+[Ee]xams)\b', 'across ' + ec + r'\1'),
        (r'\b\d+(\s+Microsoft\s+[Ee]xams)\b', ec + r'\1'),
        (r'Browse\s+the\s+\d+(\s+exams)', 'Browse the ' + ec + r'\1'),
        (r'\b\d+(\s+exams\s+spanning)', ec + r'\1'),
        # ── certification paths ──
        (r'\b\d+(\s+certification\s+paths)', cp + r'\1'),
        (r'\b\d+(\s+certification\s+routes)', cp + r'\1'),
        (r'\b\d+(\s+guided\s+certification\s+paths)', cp + r'\1'),
        # ── headline word-number "Twenty-six certifications." -> exam count word ──
        (r'(headline-accent">)[A-Za-z-]+(\s+certifications\.)',
         r'\g<1>' + number_word(exam_count) + r'\2'),
    ]


def llms_edits(counts: dict, total_label: str, exam_count: int):
    """Counts in llms.txt: the header summary + the per-exam bullet list.
    Each bullet is '...(/exams/<dir>/): <n> in-app practice questions...'."""
    ec = str(exam_count)
    edits = [
        # header: "9,000+ practice questions cover 27 Microsoft certification exams"
        (r'\b[\d,]+\+?(\s+practice\s+questions\s+cover)', total_label + r'\1'),
        (r'cover\s+\d+(\s+Microsoft\s+certification\s+exams)', 'cover ' + ec + r'\1'),
    ]
    for code, n in counts.items():
        dir_ = code_to_dir(code)
        # Use \g<N> (not \1\2) — a bare \1 followed by digits, e.g. "\1" + "358",
        # would be misread by re as group reference \1358 / \13.
        edits.append(
            (rf'(/exams/{re.escape(dir_)}/\):\s*)\d+(\s+in-app\s+practice\s+questions)',
             r'\g<1>' + str(n) + r'\g<2>'))
    return edits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true",
                    help="re-read counts from the app repo into data/exam-counts.json")
    ap.add_argument("--check", action="store_true",
                    help="report files that would change; write nothing")
    ap.add_argument("--app-repo", default=DEFAULT_APP_REPO,
                    help=f"path to the AZ-104 Mastery checkout (default: {DEFAULT_APP_REPO})")
    args = ap.parse_args()

    data = refresh_from_app(args.app_repo) if args.refresh else load_data()

    counts = {k.upper(): v for k, v in data["exams"].items()}
    total = sum(counts.values())
    exam_count = len(counts)
    cert_paths = data.get("cert_path_count") or 0
    rounded = (total // 500) * 500
    total_label = f"{rounded:,}+"      # prose, e.g. "10,000+"
    metric_total = str(rounded)        # comma-less for the count-up animation

    print(f"counts: {exam_count} exams, {total} questions "
          f"-> label {total_label} (metric {metric_total}), {cert_paths} cert paths")

    p = Patcher(check_only=args.check)

    print("exam pages:")
    for code, n in sorted(counts.items()):
        page = os.path.join(EXAMS_DIR, code_to_dir(code), "index.html")
        if not os.path.exists(page):
            print(f"  skip (missing): exams/{code_to_dir(code)}/index.html")
            continue
        # own-exam anchored edits
        original = open(page).read()
        text = original
        for pat, rep in exam_page_edits(code, n):
            text = re.sub(pat, rep, text)
        # cross-referenced related cards (any exam -> its count)
        text, _ = patch_related_cards(text, counts)
        rel = os.path.relpath(page, ROOT)
        if text != original:
            p.changed_files += 1
            if args.check:
                print(f"  DRIFT  {rel}")
            else:
                open(page, "w").write(text)
                print(f"  synced {rel}")

    print("homepage:")
    p.apply(INDEX_HTML, homepage_edits(total_label, metric_total, exam_count, cert_paths))

    print("llms.txt:")
    p.apply(LLMS_TXT, llms_edits(counts, total_label, exam_count))

    verb = "would change" if args.check else "changed"
    print(f"\n{p.changed_files} file(s) {verb}.")
    if args.check and p.changed_files:
        sys.exit(1)


if __name__ == "__main__":
    main()
