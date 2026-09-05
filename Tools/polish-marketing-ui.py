#!/usr/bin/env python3
"""Apply the shared marketing UI contracts introduced by the polish pass."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADINGS = (
    "Exam-specific practice",
    "Predicted score",
    "Adaptive study plan",
    "Knowledge decay",
    "Exam rehearsal",
    "Answer Coach",
    "Aura guidance",
    "Private by design",
)
ARTICLE_PAGES = (
    sorted((ROOT / "guides").glob("*/index.html"))
    + [ROOT / "about/index.html", ROOT / "how-exam-iq-works/index.html", ROOT / "how-we-write-questions/index.html", ROOT / "exams/retired/index.html"]
)


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).replace("\n", " ").strip()


def code_for(path: Path, section: str) -> str:
    match = re.search(r"Designed for\s+([^<]+)", section)
    if match:
        return strip_tags(match.group(1))
    if path.name == "_template.html":
        return "{{CERT_CODE}}"
    return path.parent.name.upper()


def domain_detail(first: str) -> str:
    plain = strip_tags(first)
    patterns = (
        r"(?:mapped|tagged) to (.*?)(?:, so| — so| so weak| so you|\. Each|\.)",
        r"official (\w+(?:[ -]\w+){0,10}) domains",
    )
    for pattern in patterns:
        match = re.search(pattern, plain, re.I)
        if match:
            words = match.group(1).strip(" —,.").split()
            if 2 <= len(words) <= 24:
                return "Coverage follows " + " ".join(words) + "."
    return "Domain tags help you find the topics you need to practise."


def benefit_markup(code: str, paragraphs: list[str]) -> str:
    strong = re.search(r"<strong>(.*?)</strong>", paragraphs[0], re.S)
    practice = strip_tags(strong.group(1)) if strong else f"{code} practice questions"
    duration = re.search(r"\b(?:\d{2,3}-minute|\d{2,3} minute|\{\{EXAM_DURATION_SHORT\}\})", strip_tags(paragraphs[4]), re.I)
    timed = (duration.group(0) + " session") if duration else "timed session"
    bullets = (
        (f"<strong>{html.escape(practice)}</strong> aligned to the published skills outline.", domain_detail(paragraphs[0]), "Practise decisions from the exam outline with scenarios and interactive questions."),
        (f"Exam IQ predicts your {html.escape(code)} score on-device after roughly 30 questions.", "A confidence range shows how stable the prediction is.", "See which exam objectives need the most work."),
        ("Your study plan updates as you answer questions.", "Missed topics return sooner; consistently mastered topics appear less often.", "Sessions focus on the gaps most likely to help you reach the 700 pass score."),
        ("Track which topics you're starting to forget.", "Get reminders to revisit those topics before exam day.", "Weak-spot sessions bring fading topics back into practice."),
        (f"Practise staying focused through a full {html.escape(timed)}.", "Original questions follow the published domain weighting.", "Microsoft controls the live interface and exact question mix."),
        ("Every answer has a written explanation, with reasons for individual options where available.", "See why you missed an answer, how the options differ, and what to remember.", "On supported devices, optional AI can reword notes while checking them against the written explanations."),
        ("Aura suggests what to do after each session.", "Recaps show your progress and which topics to practise next."),
        ("Practice, scoring, readiness, and coaching run on-device.", "You don't need an Azure Mastery account or a server to process your study data.", "Optional sync uses your private iCloud account."),
    )
    cards = []
    for heading, items in zip(HEADINGS, bullets):
        lis = "\n".join(f"          <li>{item}</li>" for item in items)
        cards.append(
            "      <article class=\"exam-benefit\">\n"
            f"        <h3>{heading}</h3>\n"
            "        <ul>\n"
            f"{lis}\n"
            "        </ul>\n"
            "      </article>"
        )
    return "\n".join(cards)


def rewrite_benefits(path: Path, text: str) -> str:
    match = re.search(r'(<section id="how-helps" class="container exam-feature-grid">)(.*?)(\n\s*</section>)', text, re.S)
    if not match:
        raise AssertionError(f"{path}: missing #how-helps")
    body = match.group(2)
    paragraphs = [p for attrs, p in re.findall(r"<p([^>]*)>(.*?)</p>", body, re.S) if "section-eyebrow" not in attrs]
    if len(paragraphs) == 0 and body.count('class="exam-benefit"') == 8:
        return text
    if len(paragraphs) != 8:
        raise AssertionError(f"{path}: expected 8 benefit paragraphs, found {len(paragraphs)}")
    first_card = re.search(r"\s*<p(?![^>]*section-eyebrow)[^>]*>.*", body, re.S)
    if not first_card:
        raise AssertionError(f"{path}: could not locate benefit cards")
    prefix = body[: first_card.start()]
    replacement = prefix + "\n" + benefit_markup(code_for(path, match.group(0)), paragraphs)
    return text[: match.start(2)] + replacement + text[match.end(2) :]


def add_table_labels(text: str) -> str:
    def table_repl(table_match: re.Match[str]) -> str:
        table = table_match.group(0)
        head = re.search(r"<thead>(.*?)</thead>", table, re.S)
        body = re.search(r"<tbody>(.*?)</tbody>", table, re.S)
        if not head or not body:
            return table
        headers = [strip_tags(value) for value in re.findall(r"<th[^>]*>(.*?)</th>", head.group(1), re.S)]

        def row_repl(row_match: re.Match[str]) -> str:
            row = row_match.group(0)
            offset = 1 if re.search(r"<th\b", row) else 0
            position = 0

            def cell_repl(cell_match: re.Match[str]) -> str:
                nonlocal position
                attrs, value = cell_match.groups()
                label_index = min(position + offset, len(headers) - 1)
                position += 1
                if "data-label=" in attrs or not headers:
                    return cell_match.group(0)
                label = html.escape(headers[label_index], quote=True)
                return f'<td{attrs} data-label="{label}">{value}</td>'

            return re.sub(r"<td([^>]*)>(.*?)</td>", cell_repl, row, flags=re.S)

        new_body = re.sub(r"<tr[^>]*>.*?</tr>", row_repl, body.group(1), flags=re.S)
        return table[: body.start(1)] + new_body + table[body.end(1) :]

    return re.sub(r'<table class="[^"]*guide-table[^"]*".*?</table>', table_repl, text, flags=re.S)


def add_shared_assets(text: str, article: bool) -> str:
    if article:
        text, count = re.subn(r"\n\s*<style>.*?</style>", "\n  <link rel=\"stylesheet\" href=\"/article.css\">", text, count=1, flags=re.S)
        if count != 1 and "/article.css" not in text:
            raise AssertionError("article page has no replaceable style block")
    if "/section-nav.css" not in text:
        text = text.replace("</head>", '  <link rel="stylesheet" href="/section-nav.css">\n</head>', 1)
    if "/section-nav.js" not in text:
        text = text.replace("</body>", '  <script src="/section-nav.js" defer></script>\n</body>', 1)
    return text


def main() -> None:
    exam_pages = sorted((ROOT / "exams").glob("*/index.html"))
    exam_pages = [path for path in exam_pages if path.parent.name != "retired"] + [ROOT / "exams/_template.html"]
    for path in exam_pages:
        text = rewrite_benefits(path, path.read_text())
        path.write_text(add_shared_assets(text, article=False))

    for path in ARTICLE_PAGES:
        text = add_table_labels(path.read_text())
        path.write_text(add_shared_assets(text, article=True))

    for path in [ROOT / "index.html", ROOT / "guides/index.html", ROOT / "exams/index.html"]:
        path.write_text(add_shared_assets(path.read_text(), article=False))


if __name__ == "__main__":
    main()
