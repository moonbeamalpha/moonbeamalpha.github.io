#!/usr/bin/env python3
"""Render six unchanged app-bank questions into the accessible homepage sample."""
import argparse
import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION = {"AZ-900": ("az900-q001", "az900-q054", "az900-q124"),
             "AZ-104": ("q002", "q013", "q045")}


def render(app_repo):
    catalogue = json.loads((app_repo / 'App/AzureMastery/Resources/exam-catalog.json').read_text())['exams']
    current = [e for e in catalogue if not (e.get('lifecycle') or {}).get('retirementDate')]
    assert current and min(e['freeQuestionLimit'] for e in current) >= 50, 'Free allowance copy needs review'
    cards = []
    provenance = {}
    for code, ids in SELECTION.items():
        bank_path = app_repo / f"App/AzureMastery/Resources/{code.lower().replace('-', '')}-questions.json"
        bank = {q["id"]: q for q in json.loads(bank_path.read_text())["questions"]}
        provenance[code] = []
        for position, question_id in enumerate(ids, 1):
            q = bank[question_id]
            assert q["format"] == "singleSelect" and len(q["correctAnswers"]) == 1
            assert set(q["optionRationales"]) == {o["id"] for o in q["options"]}
            esc = lambda value, **kwargs: html.escape(re.sub(r'`([^`]+)`', r'\1', value), **kwargs)
            options = []
            for option in q["options"]:
                selected = ' class="is-selected"' if option["id"] in q["correctAnswers"] else ""
                options.append(f'<li{selected}><span class="qt__option-text">{esc(option["text"])}</span><span class="qt__rationale" hidden>{esc(q["optionRationales"][option["id"]])}</span></li>')
            answer = next(o["text"] for o in q["options"] if o["id"] in q["correctAnswers"])
            cards.append(f'''<article class="qt" data-practice-card data-practice-exam="{code}" data-practice-position="{position}">
<div class="practice-preview__topline"><p class="practice-preview__code">{code}</p><span class="practice-preview__sample">Question {position} of {len(ids)}</span></div>
<p class="practice-preview__topic">{esc(q["subTopic"])} <span>· Single answer</span></p>
<div class="qt__viz" data-quiz="1" data-exam-code="{code}" data-question-id="{esc(q["id"])}"><p class="qt__viz-q">{esc(q["text"])}</p><ul class="qt__viz-options">{''.join(options)}</ul></div>
<noscript><details class="qt__answer-fallback"><summary>Read the answer and explanation</summary><p><strong>{esc(answer)}</strong> — {esc(q["explanation"])}</p></details></noscript>
<p class="practice-source"><a href="{esc(q["resourceURL"], quote=True)}" target="_blank" rel="noopener noreferrer">Microsoft Learn reference <span class="sr-only">(opens a new tab)</span></a></p>
</article>''')
            provenance[code].append({key: q.get(key, "") for key in ("id", "text", "options", "correctAnswers", "optionRationales", "explanation", "resourceURL", "objectiveID")})
    return "\n".join(cards), json.dumps(provenance, ensure_ascii=False, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-repo", type=Path, default=Path(os.environ.get("AZURE_MASTERY_APP_REPO", str(ROOT.parent / "AZ-104 Mastery"))))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cards, snapshot = render(args.app_repo)
    page = ROOT / "index.html"
    before = page.read_text()
    after, count = re.subn(r"<!-- home-practice:start -->.*?<!-- home-practice:end -->", "<!-- home-practice:start -->\n" + cards + "\n<!-- home-practice:end -->", before, flags=re.S)
    assert count == 1, "Homepage practice markers missing or duplicated"
    output = ROOT / "data/home-practice.json"
    stale = after != before or not output.exists() or output.read_text() != snapshot
    if args.check:
        if stale:
            raise SystemExit("Homepage samples are stale; run Tools/sync-home-practice.py")
    else:
        page.write_text(after)
        output.write_text(snapshot)
    print("Homepage practice samples match their app-bank sources")


if __name__ == "__main__":
    main()
