#!/usr/bin/env python3
"""Batch-patch every exam page with the conversion surfaces search-visibility
PR A calls for: a sticky mobile download bar, two mid-page CTA bands, the
exam code surfaced in the hero headline and the sticky nav, and the
standards-track `mobile-web-app-capable` meta tag alongside the existing
Apple-prefixed one. Modelled on Tools/add-theme-support.py: a list of
(anchor, replacement) edits per file; every anchor is asserted to match
exactly once before anything is written; a file that already carries the
`mobile-cta-bar` marker (or, for meta-only targets, the standalone
`mobile-web-app-capable` tag) is skipped outright so re-runs are no-ops.

    python3 Tools/add-exam-page-cta.py            # apply
    python3 Tools/add-exam-page-cta.py --check    # dry run; report only, exit 1 on drift

Targets:
  - every exams/<code>/index.html whose upper-cased code is a key in
    data/exam-counts.json["exams"] — gets the full set: sticky bar, both
    mid-page CTAs, hero code span, nav badge, deprecated meta.
  - exams/_template.html — the same full set, using {{CERT_CODE}} /
    {{CERT_CODE_LOWER}} placeholders instead of a real code.
  - exams/_hero.html — the hero code span ONLY (it is a copy-paste
    fragment, not a served page: no exam.js, no nav, no sections).
  - index.html, exams/index.html, guides/index.html, guides/*/index.html,
    404.html — the deprecated meta tag ONLY.

Known gap (see task report): five files in the meta-tag target set
(exams/gh-300, exams/gh-900, exams/_template.html, exams/index.html,
404.html) never carried `apple-mobile-web-app-capable` in the first place,
so there is nothing to insert after. The tool treats a zero-count anchor
for that one edit as "not applicable" and skips just that edit rather than
failing the file — a >1 count is still a hard failure (real drift).
"""
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
EXAMS = SITE / "exams"
CHECK = "--check" in sys.argv[1:]

STORE_BASE = "https://apps.apple.com/app/apple-store/id6760594569"

MARKER = "mobile-cta-bar"                       # idempotency marker: full-edit pages
HERO_MARKER = "am-cert-hero__lead-code"          # idempotency marker: _hero.html
META_MARKER = 'name="mobile-web-app-capable"'    # idempotency marker: meta-only pages

EXAM_JS_ANCHOR = '  <script src="/exams/exam.js" defer></script>'
THEME_TOGGLE_ANCHOR = '    <button class="theme-toggle"'
STUDY_PLAN_ANCHOR = '    <section id="study-plan" class="container">'
FAQS_ANCHOR = '    <section id="faqs" class="container">'
APPLE_META_LINE = '  <meta name="apple-mobile-web-app-capable" content="yes">'
MOBILE_WEB_META_LINE = '  <meta name="mobile-web-app-capable" content="yes">'

# Anchored on the id+class of the open tag rather than the trailing copy:
# three non-current exam pages (AI-102, AI-900, DP-100) run "Review the
# final outline." instead of "Predict your score." here, so anchoring on
# the literal lead sentence (as the brief describes) would not match those
# three files exactly once. The element itself (<p> on real/template pages,
# <h2> on _hero.html) is what "exam code in the hero headline" needs.
HERO_LEAD_RE = re.compile(r'(id="am-cert-hero-lead" class="am-cert-hero__lead">\s*\n\s*)')


def sticky_bar_html(code: str, code_lower: str) -> str:
    return (
        '  <!-- Sticky mobile download bar — the hero CTA scrolls away fast on a phone -->\n'
        '  <div class="mobile-cta-bar" id="mobile-cta-bar">\n'
        f'    <span class="mobile-cta-bar__label">{code} practice — free on the App&nbsp;Store</span>\n'
        f'    <a class="mobile-cta-bar__btn" href="{STORE_BASE}?ct=exam-{code_lower}-sticky" rel="noopener noreferrer">Download</a>\n'
        '  </div>\n'
    )


def inline_cta_html(code: str, code_lower: str, suffix: str) -> str:
    return (
        '  <aside class="exam-inline-cta" aria-label="Download Azure Mastery">\n'
        f'    <p class="exam-inline-cta__text"><strong>Ready to practise {code}?</strong> Every question explains every option, and the first sessions are free.</p>\n'
        f'    <a class="exam-inline-cta__btn" href="{STORE_BASE}?ct=exam-{code_lower}-{suffix}" rel="noopener noreferrer">Download free</a>\n'
        '  </aside>\n'
    )


def nav_badge_html(code: str) -> str:
    return f'    <span class="site-nav__context" aria-label="Exam page">{code}</span>\n'


def full_page_edits(code: str, code_lower: str) -> list[tuple[str, str]]:
    """The six anchor edits for a real exam page / _template.html."""
    return [
        (EXAM_JS_ANCHOR, sticky_bar_html(code, code_lower) + EXAM_JS_ANCHOR),
        (STUDY_PLAN_ANCHOR, inline_cta_html(code, code_lower, "mid1") + STUDY_PLAN_ANCHOR),
        (FAQS_ANCHOR, inline_cta_html(code, code_lower, "mid2") + FAQS_ANCHOR),
        (THEME_TOGGLE_ANCHOR, nav_badge_html(code) + THEME_TOGGLE_ANCHOR),
    ]


def apply_hero_span(text: str, code: str) -> tuple[str, int]:
    matches = HERO_LEAD_RE.findall(text)
    if len(matches) != 1:
        raise AssertionError(
            f'hero lead anchor matched {len(matches)} times (want 1)'
        )
    span = f'<span class="am-cert-hero__lead-code">{code}:</span> '
    new_text, n = HERO_LEAD_RE.subn(lambda m: m.group(1) + span, text, count=1)
    return new_text, n


def process_full_page(path: Path, code: str, code_lower: str) -> str:
    text = path.read_text()
    if MARKER in text:
        return "skip (already patched)"

    edits = full_page_edits(code, code_lower)
    for anchor, _ in edits:
        count = text.count(anchor)
        if count != 1:
            raise AssertionError(f"{path}: anchor {anchor[:60]!r} matched {count} times (want 1)")
    for anchor, replacement in edits:
        text = text.replace(anchor, replacement, 1)

    # Deprecated meta: best-effort. Five files in this same primary list
    # (gh-300, gh-900, _template.html) have never carried the Apple-prefixed
    # tag, so there is nothing to insert after — skip, don't fail the file.
    apple_count = text.count(APPLE_META_LINE)
    if apple_count == 1:
        text = text.replace(APPLE_META_LINE, APPLE_META_LINE + "\n" + MOBILE_WEB_META_LINE, 1)
    elif apple_count > 1:
        raise AssertionError(f"{path}: anchor {APPLE_META_LINE!r} matched {apple_count} times (want 0 or 1)")

    text, _ = apply_hero_span(text, code)

    if not CHECK:
        path.write_text(text)
    return "updated" if not CHECK else "would update"


def process_hero_fragment(path: Path) -> str:
    text = path.read_text()
    if HERO_MARKER in text:
        return "skip (already patched)"
    text, _ = apply_hero_span(text, "{{CERT_CODE}}")
    if not CHECK:
        path.write_text(text)
    return "updated" if not CHECK else "would update"


def process_meta_only(path: Path) -> str:
    text = path.read_text()
    if META_MARKER in text:
        return "skip (already has mobile-web-app-capable)"
    apple_count = text.count(APPLE_META_LINE)
    if apple_count == 0:
        return "skip (no apple-mobile-web-app-capable anchor)"
    if apple_count > 1:
        raise AssertionError(f"{path}: anchor {APPLE_META_LINE!r} matched {apple_count} times (want 0 or 1)")
    text = text.replace(APPLE_META_LINE, APPLE_META_LINE + "\n" + MOBILE_WEB_META_LINE, 1)
    if not CHECK:
        path.write_text(text)
    return "updated" if not CHECK else "would update"


def main() -> int:
    with open(SITE / "data" / "exam-counts.json") as f:
        exam_codes = set(json.load(f)["exams"].keys())

    primary_targets: list[tuple[Path, str, str]] = []
    for d in sorted(p for p in EXAMS.iterdir() if p.is_dir()):
        code = d.name.upper()
        if code not in exam_codes:
            continue
        index = d / "index.html"
        if index.exists():
            primary_targets.append((index, code, d.name.lower()))
    template = EXAMS / "_template.html"
    if template.exists():
        primary_targets.append((template, "{{CERT_CODE}}", "{{CERT_CODE_LOWER}}"))

    hero_fragment = EXAMS / "_hero.html"

    meta_only_targets = [SITE / "index.html", EXAMS / "index.html", SITE / "guides" / "index.html", SITE / "404.html"]
    meta_only_targets += sorted((SITE / "guides").glob("*/index.html"))

    results: list[tuple[str, str]] = []
    failures: list[str] = []

    for path, code, code_lower in primary_targets:
        label = str(path.relative_to(SITE))
        try:
            results.append((label, process_full_page(path, code, code_lower)))
        except AssertionError as exc:
            failures.append(str(exc))
            results.append((label, "FAILED"))

    if hero_fragment.exists():
        label = str(hero_fragment.relative_to(SITE))
        try:
            results.append((label, process_hero_fragment(hero_fragment)))
        except AssertionError as exc:
            failures.append(str(exc))
            results.append((label, "FAILED"))

    for path in meta_only_targets:
        if not path.exists():
            continue
        label = str(path.relative_to(SITE))
        try:
            results.append((label, process_meta_only(path)))
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
