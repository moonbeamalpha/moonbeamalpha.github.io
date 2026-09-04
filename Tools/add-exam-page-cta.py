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

Deprecated meta (fix round 1, item 1): every target in both lists gets
BOTH `apple-mobile-web-app-capable` and `mobile-web-app-capable`, no
exceptions. Five files (exams/gh-300, exams/gh-900, exams/_template.html,
exams/index.html, 404.html) never carried the Apple-prefixed tag at all;
for those, both lines are inserted together immediately after the page's
`<meta name="viewport" …>` line instead. The viewport anchor is asserted
to match exactly once (strict — no 0-or-1 branch) before anything is
written, same as every other anchor here.

Retired-exam copy (fix round 1 item 3, fix round 2 small item): a code in
data/exam-counts.json["retired"] (currently AI-102, AI-900, AZ-204,
AZ-500, DP-100) gets different mid-page CTA copy and sticky-bar label —
"Ready to practise" / "practice" both contradict the retirement banner
already on that page. Re-running the tool against pages patched by an
earlier version with the old copy detects and rewrites just that text
(the file's `mobile-cta-bar` marker still short-circuits everything
else), so the tool stays idempotent either way.
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
VIEWPORT_ANCHOR = '  <meta name="viewport" content="width=device-width, initial-scale=1.0">'

with open(SITE / "data" / "exam-counts.json") as _f:
    _EXAM_COUNTS = json.load(_f)
EXAM_CODES = set(_EXAM_COUNTS["exams"].keys())
RETIRED_CODES = set(_EXAM_COUNTS.get("retired", []))

# Anchored on the id+class of the open tag rather than the trailing copy:
# three non-current exam pages (AI-102, AI-900, DP-100) run "Review the
# final outline." instead of "Predict your score." here, so anchoring on
# the literal lead sentence (as the brief describes) would not match those
# three files exactly once. The element itself (<p> on real/template pages,
# <h2> on _hero.html) is what "exam code in the hero headline" needs.
HERO_LEAD_RE = re.compile(r'(id="am-cert-hero-lead" class="am-cert-hero__lead">\s*\n\s*)')


def sticky_bar_label(code: str, retired: bool) -> str:
    """Text inside .mobile-cta-bar__label. Retired codes (data/exam-counts
    .json["retired"]) get "reference bank" instead of "practice" — same
    reasoning as cta_copy(): "practice" contradicts the retirement banner
    already on that page."""
    if retired:
        return f'{code} reference bank — free on the App&nbsp;Store'
    return f'{code} practice — free on the App&nbsp;Store'


def sticky_bar_html(code: str, code_lower: str, retired: bool) -> str:
    return (
        '  <!-- Sticky mobile download bar — the hero CTA scrolls away fast on a phone -->\n'
        '  <div class="mobile-cta-bar" id="mobile-cta-bar">\n'
        f'    <span class="mobile-cta-bar__label">{sticky_bar_label(code, retired)}</span>\n'
        f'    <a class="mobile-cta-bar__btn" href="{STORE_BASE}?ct=exam-{code_lower}-sticky" rel="noopener noreferrer">Download</a>\n'
        '  </div>\n'
    )


def cta_copy(code: str, retired: bool) -> str:
    """The <strong>…</strong> lead + follow-on sentence inside the mid-page
    CTA's <p>. Retired codes (data/exam-counts.json["retired"]) get copy
    that doesn't contradict the retirement banner already on that page."""
    if retired:
        return (
            f'<strong>Reviewing {code} as reference?</strong> The app keeps the retired '
            'bank alongside the current exams, and the first sessions are free.'
        )
    return (
        f'<strong>Ready to practise {code}?</strong> Every question explains every option, '
        'and the first sessions are free.'
    )


def inline_cta_html(code: str, code_lower: str, suffix: str, retired: bool) -> str:
    return (
        '  <aside class="exam-inline-cta" aria-label="Download Azure Mastery">\n'
        f'    <p class="exam-inline-cta__text">{cta_copy(code, retired)}</p>\n'
        f'    <a class="exam-inline-cta__btn" href="{STORE_BASE}?ct=exam-{code_lower}-{suffix}" rel="noopener noreferrer">Download free</a>\n'
        '  </aside>\n'
    )


def nav_badge_html(code: str) -> str:
    return f'    <span class="site-nav__context" aria-label="Exam page">{code}</span>\n'


def full_page_edits(code: str, code_lower: str, retired: bool) -> list[tuple[str, str]]:
    """The four anchor edits for a real exam page / _template.html (the
    deprecated meta and hero-code span are handled separately — see
    insert_deprecated_meta() and apply_hero_span())."""
    return [
        (EXAM_JS_ANCHOR, sticky_bar_html(code, code_lower, retired) + EXAM_JS_ANCHOR),
        (STUDY_PLAN_ANCHOR, inline_cta_html(code, code_lower, "mid1", retired) + STUDY_PLAN_ANCHOR),
        (FAQS_ANCHOR, inline_cta_html(code, code_lower, "mid2", retired) + FAQS_ANCHOR),
        (THEME_TOGGLE_ANCHOR, nav_badge_html(code) + THEME_TOGGLE_ANCHOR),
    ]


def rewrite_retired_cta_copy(text: str, code: str) -> tuple[str, bool]:
    """For a page already patched with the old (wrong) 'Ready to practise'
    copy, rewrite both mid-page CTA <p> bodies to the retired-appropriate
    copy. Returns (text, changed) — changed is False once already rewritten,
    so re-running this is a no-op (idempotent)."""
    old = cta_copy(code, retired=False)
    if old not in text:
        return text, False
    new = cta_copy(code, retired=True)
    return text.replace(old, new), True


def rewrite_retired_sticky_label(text: str, code: str) -> tuple[str, bool]:
    """Same idea as rewrite_retired_cta_copy() but for the sticky bar's
    .mobile-cta-bar__label text."""
    old = sticky_bar_label(code, retired=False)
    if old not in text:
        return text, False
    new = sticky_bar_label(code, retired=True)
    return text.replace(old, new), True


def insert_deprecated_meta(text: str, path: Path) -> str:
    """Insert mobile-web-app-capable alongside apple-mobile-web-app-capable.
    Every target ends up with exactly one of each — no skip branch. Pages
    that already carry the Apple-prefixed tag get the standards tag right
    after it (existing behaviour); pages that never had it (gh-300, gh-900,
    _template.html, exams/index.html, 404.html) get both lines inserted
    together right after <meta name="viewport" …>, asserted to match
    exactly once first."""
    apple_count = text.count(APPLE_META_LINE)
    if apple_count == 1:
        return text.replace(APPLE_META_LINE, APPLE_META_LINE + "\n" + MOBILE_WEB_META_LINE, 1)
    if apple_count == 0:
        viewport_count = text.count(VIEWPORT_ANCHOR)
        if viewport_count != 1:
            raise AssertionError(f"{path}: anchor {VIEWPORT_ANCHOR!r} matched {viewport_count} times (want 1)")
        return text.replace(
            VIEWPORT_ANCHOR,
            VIEWPORT_ANCHOR + "\n" + APPLE_META_LINE + "\n" + MOBILE_WEB_META_LINE,
            1,
        )
    raise AssertionError(f"{path}: anchor {APPLE_META_LINE!r} matched {apple_count} times (want 0 or 1)")


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
    retired = code in RETIRED_CODES

    if MARKER in text:
        # Already patched by an earlier run of this tool. Things an earlier
        # version could have gotten wrong on an already-patched file
        # without touching anything else: the deprecated meta was skipped
        # outright when the Apple-prefixed tag was absent (gh-300, gh-900,
        # _template.html), and a retired code still carries the stale
        # "Ready to practise" mid-CTA copy and/or "practice" sticky-bar
        # label. Detect and fix whichever apply; if none do, the file is
        # fully up to date.
        changes = []
        if META_MARKER not in text:
            text = insert_deprecated_meta(text, path)
            changes.append("meta")
        if retired:
            text, copy_changed = rewrite_retired_cta_copy(text, code)
            if copy_changed:
                changes.append("retired CTA copy")
            text, label_changed = rewrite_retired_sticky_label(text, code)
            if label_changed:
                changes.append("retired sticky label")
        if not changes:
            return "skip (already patched)"
        if not CHECK:
            path.write_text(text)
        label = ", ".join(changes)
        return f"updated ({label})" if not CHECK else f"would update ({label})"

    edits = full_page_edits(code, code_lower, retired)
    for anchor, _ in edits:
        count = text.count(anchor)
        if count != 1:
            raise AssertionError(f"{path}: anchor {anchor[:60]!r} matched {count} times (want 1)")
    for anchor, replacement in edits:
        text = text.replace(anchor, replacement, 1)

    text = insert_deprecated_meta(text, path)
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
    text = insert_deprecated_meta(text, path)
    if not CHECK:
        path.write_text(text)
    return "updated" if not CHECK else "would update"


def main() -> int:
    primary_targets: list[tuple[Path, str, str]] = []
    for d in sorted(p for p in EXAMS.iterdir() if p.is_dir()):
        code = d.name.upper()
        if code not in EXAM_CODES:
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
