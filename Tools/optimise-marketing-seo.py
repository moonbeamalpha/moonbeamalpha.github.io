#!/usr/bin/env python3
"""Keep exam-page SEO and preview content aligned with the app.

This performs the repeatable, site-wide parts of the Search Console cleanup:

* concise, query-led title tags and descriptions;
* accurate question counts in metadata, schema and body copy;
* useful, exam-specific question previews sourced from the in-app banks;
* clean SoftwareApplication keywords and evergreen feature claims;
* consistent Answer Coach naming and privacy-safe provenance;
* matching JSON-LD and sitemap modification dates.

The exam-specific editorial copy remains in each HTML page. Run this after
question-bank updates so newly published pages do not inherit generic Azure
examples or stale metadata.

Usage:
  python3 Tools/optimise-marketing-seo.py
  python3 Tools/optimise-marketing-seo.py --check
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXAMS_DIR = ROOT / "exams"
DATA_FILE = ROOT / "data" / "exam-counts.json"
SITEMAP = ROOT / "sitemap.xml"
SEO_UPDATED = "2026-07-21"
RETIRED_EXAMS = {
    "AI-900": {
        "date": "30 June 2026",
        "replacement": "AI-901",
        "replacement_label": "the current Azure AI Fundamentals exam",
    },
    "AI-102": {
        "date": "30 June 2026",
        "replacement": "AI-103",
        "replacement_label": "the current Azure AI apps and agents exam",
    },
    "DP-100": {
        "date": "1 June 2026",
        "replacement": "AI-300",
        "replacement_label": "a current machine-learning operations option",
    },
}
DEFAULT_APP_REPO = Path(
    os.environ.get("AZURE_MASTERY_APP_REPO", ROOT.parent / "AZ-104 Mastery")
)


def code_to_resource_name(code: str) -> str:
    return code.lower().replace("-", "") + "-questions.json"


def clean_text(value: str, limit: int | None = None) -> str:
    """Turn question-bank Markdown-ish prose into safe, compact HTML text."""
    value = re.sub(r"`([^`]+)`", r"\1", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    if limit and len(value) > limit:
        value = value[: limit - 1].rsplit(" ", 1)[0] + "…"
    return html.escape(value, quote=False)


def choose_question(questions: list[dict], format_name: str, *, options: bool = False) -> dict:
    candidates = [q for q in questions if q.get("format") == format_name]
    if options:
        candidates = [
            q for q in candidates
            if 3 <= len(q.get("options", [])) <= 6
            and all(len(o.get("text", "")) <= 105 for o in q.get("options", []))
        ]
    if not candidates:
        raise ValueError(f"question bank has no usable {format_name} sample")
    return min(
        candidates,
        key=lambda q: len(q.get("text", ""))
        + sum(len(o.get("text", "")) for o in q.get("options", [])),
    )


def option_list(question: dict, marker: str) -> str:
    correct = set(question.get("correctAnswers", []))
    items = []
    for option in question.get("options", []):
        selected = ' class="is-selected"' if option.get("id") in correct else ""
        items.append(
            f'              <li{selected}><span class="qt__viz-{marker}"></span>'
            f'{clean_text(option.get("text", ""), 90)}</li>'
        )
    return "\n".join(items)


def drag_sample(questions: list[dict]) -> tuple[str, list[str], str]:
    drag = next((q for q in questions if q.get("format") == "dragAndDrop" and q.get("options")), None)
    if drag:
        by_id = {o.get("id"): o.get("text", "") for o in drag.get("options", [])}
        ordered = [by_id[a] for a in drag.get("correctAnswers", []) if a in by_id]
        if len(ordered) < 3:
            ordered = [o.get("text", "") for o in drag.get("options", [])]
        return clean_text(drag.get("text", ""), 155), ordered[:5], "Drag-and-drop"

    match = choose_question(questions, "dragToMatch")
    sentences = [
        s.strip() for s in re.split(r"(?<=[.!?])\s+", match.get("explanation", ""))
        if len(s.strip()) > 15
    ]
    if len(sentences) < 3:
        sentences = [q.get("subTopic", q.get("domain", "Exam item")) for q in questions[:4]]
    return clean_text(match.get("text", ""), 155), sentences[:4], "Drag to match"


def interactive_sample(questions: list[dict]) -> tuple[str, str, str]:
    labels = {
        "hotArea": ("Hotspot", "Tap target"),
        "dropdownSelect": ("Dropdown selection", "Choose in context"),
        "dragToMatch": ("Drag to match", "Match concepts"),
    }
    for format_name in labels:
        sample = next((q for q in questions if q.get("format") == format_name), None)
        if sample:
            title, hint = labels[format_name]
            return clean_text(sample.get("text", ""), 170), title, hint
    raise ValueError("question bank has no interactive sample")


def case_sample(questions: list[dict]) -> tuple[str, str, list[str]]:
    case = choose_question(questions, "caseStudy")
    title = re.sub(r"^Case Study:\s*", "", case.get("text", ""), flags=re.I)
    sections = case.get("formatData", {}).get("sections", [])
    background = next(
        (s.get("content", "") for s in sections if s.get("title", "").lower() == "background"),
        case.get("explanation", ""),
    )
    by_id = {q.get("id"): q for q in questions}
    prompts = [
        by_id[qid].get("text", "")
        for qid in case.get("formatData", {}).get("subQuestionIDs", [])
        if qid in by_id
    ]
    if not prompts:
        requirements = next(
            (s.get("content", "") for s in sections if s.get("title", "").lower() == "requirements"),
            "",
        )
        prompts = [re.sub(r"^\d+[.)]\s*", "", line) for line in requirements.splitlines() if line.strip()]
    return clean_text(title, 80), clean_text(background, 170), prompts[:4]


def preview_articles(code: str, questions: list[dict]) -> str:
    single = choose_question(questions, "singleSelect", options=True)
    multi = choose_question(questions, "multiSelect", options=True)
    drag_prompt, drag_items, drag_title = drag_sample(questions)
    interactive_prompt, interactive_title, interactive_hint = interactive_sample(questions)
    case_title, case_background, case_prompts = case_sample(questions)
    case_intro = f"<strong>{case_title}</strong>" + (f" {case_background}" if case_background else "")

    single_correct = set(single.get("correctAnswers", []))
    wrong = next(o for o in single.get("options", []) if o.get("id") not in single_correct)
    rationale = single.get("optionRationales", {}).get(wrong.get("id"), single.get("explanation", ""))

    drag_html = "\n".join(
        '              <li><span class="qt__viz-drag-handle">⋮⋮</span>'
        f'<span class="qt__viz-drag-num">{i}</span>{clean_text(item, 72)}</li>'
        for i, item in enumerate(drag_items, 1)
    )
    case_html = "\n".join(
        '                <li><span class="qt__viz-case-num">'
        f'{i}</span>{clean_text(prompt, 82)}</li>'
        for i, prompt in enumerate(case_prompts, 1)
    )

    return f'''      <div class="question-types" data-preview-source="in-app-question-bank">

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <p class="qt__viz-q">{clean_text(single.get("text", ""), 175)}</p>
            <ul class="qt__viz-options">
{option_list(single, "radio")}
            </ul>
          </div>
          <h3>Multiple choice</h3>
          <p>A real {code} question-bank example with one correct answer. The app explains every option after you answer.</p>
          <span class="qt__hint">Exam-specific sample</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <p class="qt__viz-q">{clean_text(multi.get("text", ""), 175)}</p>
            <ul class="qt__viz-options">
{option_list(multi, "checkbox")}
            </ul>
          </div>
          <h3>Multi-select</h3>
          <p>A real {code} multi-select item. Every required selection must be correct to earn the mark.</p>
          <span class="qt__hint">All-or-nothing</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <p class="qt__viz-q">{drag_prompt}</p>
            <ul class="qt__viz-drag">
{drag_html}
            </ul>
          </div>
          <h3>{drag_title}</h3>
          <p>A real {code} interactive-format prompt, rendered for touch on iPhone and iPad.</p>
          <span class="qt__hint">Interactive item</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <p class="qt__viz-q">{interactive_prompt}</p>
            <div class="qt__viz-hotspot">
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--1"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--2"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--3"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--4"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--5"></span>
              <span class="qt__viz-target"></span>
            </div>
          </div>
          <h3>{interactive_title}</h3>
          <p>A real {code} prompt that tests recognition inside a visual or contextual interface.</p>
          <span class="qt__hint">{interactive_hint}</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <div class="qt__viz-case">
              <div class="qt__viz-case-scenario">
                {case_intro}
              </div>
              <ul class="qt__viz-case-questions">
{case_html}
              </ul>
            </div>
          </div>
          <h3>Case studies</h3>
          <p>A real {code} case-study scenario with linked questions that share the same requirements and environment.</p>
          <span class="qt__hint">Multi-question</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <div class="qt__viz-ai-wrong"><span class="qt__viz-ai-wrong-mark">✕</span>Your answer: {clean_text(wrong.get("text", ""), 72)}</div>
            <div class="qt__viz-ai-explain">
              <span class="qt__viz-ai-explain-mark">✨ Answer Coach:</span>{clean_text(rationale, 210)}
              <span class="qt__viz-ai-source">— grounded in authored certification guidance</span>
            </div>
          </div>
          <h3>Answer Coach</h3>
          <p>Answer Coach uses the bank's authored rationale to explain the misconception, key distinction, and rule to remember. On supported devices, an optional on-device model may rewrite the note only when it passes grounding checks.</p>
          <span class="qt__hint qt__hint--purple">App exclusive</span>
        </article>

      </div>'''


def replace_once(text: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    text, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"expected one {label} replacement, found {count}")
    return text


def update_page(text: str, code: str, count: int, questions: list[dict]) -> str:
    retired = RETIRED_EXAMS.get(code)
    if retired:
        replacement = retired["replacement"]
        title = f"{code} Retired Exam & {replacement} Next Step | Azure Mastery"
        description = (
            f"{code} retired on {retired['date']}. Review {count} practice questions and learn "
            f"about {replacement}, {retired['replacement_label']}."
        )
        social_description = (
            f"{code} retired on {retired['date']}. Keep {count} reference practice questions "
            f"and compare {replacement}, {retired['replacement_label']}."
        )
        h1 = f"{code} Retired Exam Practice &amp; Next Steps"
        feature_claim = f"{count} {code} reference practice questions mapped to the final Microsoft skills outline"
    else:
        title = f"{code} Practice Questions & Exam Prep | Azure Mastery"
        description = (
            f"Prepare for {code} with {count} practice questions, private Answer Coach, adaptive "
            "study plans, and an exam simulator for iPhone and iPad."
        )
        social_description = (
            f"{count} {code} practice questions, private Answer Coach, adaptive study plans, "
            "and a full exam simulator. Free to start."
        )
        h1 = f"{code} Practice Questions &amp; Exam Prep"
        feature_claim = f"{count} {code} practice questions mapped to the current Microsoft skills outline"
    keywords = (
        f"{code}, {code} practice questions, {code} exam prep, {code} practice test, "
        "Microsoft certification, iOS study app"
    )
    schema_keywords = (
        f"{code}, {code} practice questions, {code} exam prep, {code} mock exam, "
        "Microsoft certification, iOS study app, Answer Coach, adaptive study plan, exam score prediction"
    )

    text = replace_once(text, r"<title>.*?</title>", f"<title>{title}</title>", "title")
    text = replace_once(
        text, r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{description}">', "meta description",
    )
    text = replace_once(
        text, r'<meta name="keywords" content="[^"]*">',
        f'<meta name="keywords" content="{keywords}">', "meta keywords",
    )
    text = replace_once(
        text, r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{title}">', "OpenGraph title",
    )
    text = replace_once(
        text, r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{social_description}">', "OpenGraph description",
    )
    text = replace_once(
        text, r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{title}">', "Twitter title",
    )
    text = replace_once(
        text, r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="{social_description}">', "Twitter description",
    )
    text = replace_once(
        text,
        r'("@type": "WebPage",.*?"name": ")[^"]*(",\s*"description": ")[^"]*(")',
        lambda m: m.group(1) + title.replace(" | Azure Mastery", "") + m.group(2) + description + m.group(3),
        "WebPage name and description",
        flags=re.S,
    )
    text = replace_once(
        text, r'("dateModified": ")\d{4}-\d{2}-\d{2}("\s*,)',
        rf'\g<1>{SEO_UPDATED}\2', "dateModified",
    )
    text = replace_once(
        text, r'("keywords": ")[^"]*("\s*,\s*"featureList")',
        lambda m: m.group(1) + schema_keywords + m.group(2),
        "SoftwareApplication keywords",
        flags=re.S,
    )
    text = replace_once(
        text, rf'("featureList": \[\s*")\d+\s+{re.escape(code)}[^\"]*(")',
        rf'\g<1>{feature_claim}\2',
        "featureList question claim",
        flags=re.S,
    )
    if '"Private Answer Coach grounded in authored rationales"' not in text:
        text = replace_once(
            text,
            r'(\n\s*)("Knowledge decay tracking)',
            r'\1"Private Answer Coach grounded in authored rationales",\1\2',
            "Answer Coach feature claim",
            flags=re.S,
        )

    if "<strong>Answer Coach</strong>" not in text:
        answer_coach_copy = '''      <p>
        <strong>Answer Coach</strong> turns each missed answer into a private, grounded lesson: the misconception, key distinction, and rule to remember. It always uses authored certification guidance; on supported devices, an optional on-device model may rewrite the note only when it passes grounding checks.
      </p>
      <p>
        During your first week, <strong>Aura</strong> adapts the next step as you go. Every session ends with a concise recap of what changed, what to focus on, and the best follow-up.
      </p>
'''
        text = replace_once(
            text,
            r'(      <p>\s*Everything runs <strong>on-device</strong>\.)',
            answer_coach_copy + r'\1',
            "Answer Coach and Aura product copy",
            flags=re.S,
        )

    text = text.replace(
        "Everything runs <strong>on-device</strong>. Your answer history, your readiness gauge, your decay alerts — none of it leaves your iPhone or iPad. No account required to start, no tracking, no sync server. Privacy-first by design.",
        "Everything essential runs <strong>on-device</strong>. Your answer history, readiness gauge, and coaching stay private. Optional sync uses your private iCloud account; there is no Azure Mastery account, tracking, or external processing server.",
    )
    text = text.replace(
        " — all without sending a single byte off your device.",
        ". Core study stays on-device and works offline; optional sync uses your private iCloud account.",
    )
    text = text.replace(
        " All without sending a single byte off your device.",
        " Core study stays on-device and works offline; optional sync uses your private iCloud account.",
    )
    text = text.replace(
        "Everything runs on-device: your answer history and readiness gauge never leave your iPhone or iPad.",
        "Core study runs on-device and works offline; optional sync uses your private iCloud account.",
    )
    text = text.replace("/* Why Wrong AI */", "/* Answer Coach */")

    # Count corrections not covered by the existing sync script.
    text = re.sub(r"(full\s+)\d+(-question\s+bank)", rf"\g<1>{count}\2", text)

    # Make the visible primary heading match the high-intent query language.
    text = replace_once(
        text,
        rf'(<h1 class="display-large page-h1">\s*){re.escape(code)}.*?(—\s*<span class="page-h1-accent">)',
        rf'\g<1>{h1} \2',
        "page H1",
        flags=re.S,
    )

    # The two GitHub exam pages use a shorter layout without a preview section.
    if '<section id="question-types"' in text:
        preview = preview_articles(code, questions)
        text = replace_once(
            text,
            r'      <div class="question-types"(?: data-preview-source="[^"]+")?>.*?      </div>\s*</section>',
            preview + "\n    </section>",
            "question preview section",
            flags=re.S,
        )
    return text


def update_sitemap(text: str, codes: list[str]) -> str:
    for code in codes:
        slug = code.lower()
        pattern = (
            rf'(<url>\s*<loc>https://azuremastery\.app/exams/{re.escape(slug)}/</loc>'
            rf'.*?<lastmod>)\d{{4}}-\d{{2}}-\d{{2}}(</lastmod>\s*</url>)'
        )
        text, count = re.subn(pattern, rf'\g<1>{SEO_UPDATED}\2', text, flags=re.S)
        if count != 1:
            raise ValueError(f"expected one sitemap entry for {code}, found {count}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing files")
    parser.add_argument("--app-repo", type=Path, default=DEFAULT_APP_REPO)
    args = parser.parse_args()

    counts = json.loads(DATA_FILE.read_text())["exams"]
    changed: list[Path] = []

    for code, count in sorted(counts.items()):
        page = EXAMS_DIR / code.lower() / "index.html"
        resource = args.app_repo / "App" / "AzureMastery" / "Resources" / code_to_resource_name(code)
        if not page.exists() or not resource.exists():
            sys.exit(f"missing page or question bank for {code}: {page} / {resource}")
        questions = json.loads(resource.read_text())["questions"]
        before = page.read_text()
        after = update_page(before, code, count, questions)
        if after != before:
            changed.append(page)
            if not args.check:
                page.write_text(after)

    before = SITEMAP.read_text()
    after = update_sitemap(before, sorted(counts))
    if after != before:
        changed.append(SITEMAP)
        if not args.check:
            SITEMAP.write_text(after)

    if changed:
        verb = "would update" if args.check else "updated"
        print(f"{verb} {len(changed)} files:")
        for path in changed:
            print(f"  {path.relative_to(ROOT)}")
        if args.check:
            sys.exit(1)
    else:
        print("SEO metadata, previews, and sitemap are in sync.")


if __name__ == "__main__":
    main()
