#!/usr/bin/env python3
"""Keep every exam and guide page's FAQPage JSON-LD in lockstep with its visible FAQ
text. Google requires FAQ structured data to match the visible page content;
these pages drifted because the JSON-LD was hand-authored once alongside the
visible `<details class="faq">` markup and the two were never mechanically
kept in sync -- contractions get expanded, em-dashes get swapped for hyphens,
and the odd clause goes missing entirely.

Modelled on Tools/add-footer-links.py and Tools/add-exam-page-cta.py: no
third-party dependencies, an explicit --check that reports drift and exits
non-zero, and a surgical string edit rather than a full JSON re-dump -- only
the `name` and `acceptedAnswer.text` values that actually differ are
rewritten in place, so the file's existing JSON-LD indentation and formatting
survive untouched.

Parsing/normalisation mirrors normalise_visible_text() in
Tools/validate-marketing-seo.py (the same check that already runs for guide
and trust-page FAQs): tags stripped, HTML entities unescaped, whitespace
collapsed to single spaces. FAQ question/answer pairs are read from the
`<details class="faq"><summary>...</summary><div class="faq__answer">
<p>...</p></div></details>` blocks -- the exam-page FAQ markup, one paragraph
per answer, which is a different (but consistent) layout from the single-line
`<div class="faq__answer"><p>...</p></div>` guides use. The same expression
supports both layouts.

Guard: a page's visible FAQ count must equal its FAQPage `mainEntity` entry
count, paired in document order. A page that fails this (a hand-edit added or
removed one side without the other) is reported as a hard error and left
unwritten -- there is no safe way to guess which visible item corresponds to
which schema entry once the counts disagree.

Targets: every exams/<code>/index.html whose directory is an exam code in
data/exam-counts.json, the retired hub and exams/_template.html when they
carry FAQPage nodes, plus every guides/*/index.html carrying FAQPage markup.

    python3 Tools/sync-exam-faq-schema.py            # apply
    python3 Tools/sync-exam-faq-schema.py --check    # dry run; report only, exit 1 on drift

Run this after editing any exam-page or guide FAQ (visible copy, JSON-LD, or both).
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "exam-counts.json"
CHECK = "--check" in sys.argv[1:]

FAQ_BLOCK_RE = re.compile(
    r'<details class="faq">\s*<summary>(.*?)</summary>\s*'
    r'<div class="faq__answer">\s*<p>(.*?)</p>\s*</div>\s*</details>',
    re.S,
)

QUESTION_RE = re.compile(
    r'"@type":\s*"Question",\s*"name":\s*"(?P<name>.*?)",\s*'
    r'"acceptedAnswer":\s*\{\s*"@type":\s*"Answer",\s*"text":\s*"(?P<text>.*?)"\s*\}',
    re.S,
)


class FaqSyncError(Exception):
    """A page's visible FAQ count and JSON-LD entry count disagree -- there is
    no safe pairing to sync, so the page is reported and left untouched."""


def normalise(markup: str) -> str:
    """Strip tags, unescape entities, collapse whitespace -- same approach as
    normalise_visible_text() in Tools/validate-marketing-seo.py."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", markup)).split())


def json_inner(value: str) -> str:
    """Encode `value` as the interior of a JSON string (no surrounding
    quotes), preserving literal Unicode (em-dashes, currency symbols, curly
    punctuation) rather than escaping to \\uXXXX, matching this file's
    existing serialisation style."""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def target_pages() -> list[Path]:
    data = json.loads(DATA_FILE.read_text())
    codes = sorted(data["exams"])
    pages = [ROOT / "exams" / code.lower() / "index.html" for code in codes]
    missing = [page for page in pages if not page.exists()]
    for page in missing:
        print(f"note: {page.relative_to(ROOT)} not found (code in snapshot, page not yet added)")
    pages = [page for page in pages if page.exists()]
    # Hub and template carry FAQPage nodes too: keep them in lockstep as well.
    for extra in (ROOT / "exams" / "retired" / "index.html", ROOT / "exams" / "_template.html"):
        if extra.exists() and '"@type": "FAQPage"' in extra.read_text():
            pages.append(extra)
    for guide in sorted((ROOT / "guides").glob("*/index.html")):
        if '"@type": "FAQPage"' in guide.read_text():
            pages.append(guide)
    return pages


def process(path: Path) -> tuple[str, list[str]]:
    """Returns (status, notes). status is one of "ok", "updated" (or "would
    update" under --check). Raises FaqSyncError on a count mismatch."""
    rel = str(path.relative_to(ROOT))
    text = path.read_text()

    visible = FAQ_BLOCK_RE.findall(text)
    visible_qas = [(normalise(q), normalise(a)) for q, a in visible]
    # Scan only from the FAQPage node onwards so a Question node that belongs
    # to some other schema block earlier in the file can never be paired with
    # a visible FAQ.
    faq_start = text.find('"@type": "FAQPage"')
    if faq_start < 0:
        raise FaqSyncError(f"{rel}: no FAQPage node found")
    matches = list(QUESTION_RE.finditer(text, faq_start))

    if len(visible_qas) != len(matches):
        raise FaqSyncError(
            f"{rel}: visible FAQ count ({len(visible_qas)}) does not match the "
            f"FAQPage mainEntity count ({len(matches)}) -- fix the page by hand "
            f"before re-running this tool"
        )

    edits: list[tuple[int, int, str]] = []
    notes: list[str] = []
    for position, (m, (want_name, want_text)) in enumerate(zip(matches, visible_qas), start=1):
        try:
            have_name = json.loads(f'"{m.group("name")}"')
            have_text = json.loads(f'"{m.group("text")}"')
        except json.JSONDecodeError as exc:
            raise FaqSyncError(f"{rel}: question {position}: could not decode existing JSON-LD string: {exc}")
        if have_name != want_name:
            edits.append((m.start("name"), m.end("name"), json_inner(want_name)))
            notes.append(f"{rel}: question {position} name differs from visible text")
        if have_text != want_text:
            edits.append((m.start("text"), m.end("text"), json_inner(want_text)))
            notes.append(f"{rel}: question {position} answer differs from visible text")

    if not edits:
        return "ok", []

    new_text = text
    for start, end, repl in sorted(edits, key=lambda e: e[0], reverse=True):
        new_text = new_text[:start] + repl + new_text[end:]

    if not CHECK:
        path.write_text(new_text)
    return ("would update" if CHECK else "updated"), notes


def main() -> int:
    results: list[tuple[str, str]] = []
    all_notes: list[str] = []
    errors: list[str] = []

    for path in target_pages():
        rel = str(path.relative_to(ROOT))
        try:
            status, notes = process(path)
        except FaqSyncError as exc:
            results.append((rel, "FAILED"))
            errors.append(str(exc))
            continue
        results.append((rel, status))
        all_notes.extend(notes)

    width = max(len(label) for label, _ in results)
    for label, status in results:
        print(f"{label:{width}s}  {status}")

    if all_notes:
        print()
        for note in all_notes:
            print(f"  DIFF  {note}")

    changed = sum(1 for _, status in results if status in ("updated", "would update"))
    print(f"\n{len(results)} page(s) checked, {changed} changed, {len(errors)} error(s)")

    if errors:
        print()
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    if CHECK and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
