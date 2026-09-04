#!/usr/bin/env python3
"""Dependency-free structural gate for shared marketing UI contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADINGS = (
    "Exam-specific practice", "Predicted score", "Adaptive study plan", "Knowledge decay",
    "Exam rehearsal", "Answer Coach", "Aura guidance", "Private by design",
)


def words(value: str) -> int:
    return len(re.findall(r"[\w’'-]+", re.sub(r"<[^>]+>", " ", value)))


def main() -> int:
    errors: list[str] = []
    pages = sorted((ROOT / "exams").glob("*/index.html"))
    pages = [path for path in pages if path.parent.name != "retired"]
    for path in pages + [ROOT / "exams/_template.html"]:
        text = path.read_text()
        section = re.search(r'<section id="how-helps" class="container exam-feature-grid">.*?</section>', text, re.S)
        if not section:
            errors.append(f"{path.relative_to(ROOT)}: missing #how-helps")
            continue
        cards = re.findall(r'<article class="exam-benefit">(.*?)</article>', section.group(0), re.S)
        if len(cards) != 8:
            errors.append(f"{path.relative_to(ROOT)}: {len(cards)} benefit cards; expected 8")
            continue
        headings = tuple(re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", card, re.S).group(1)).strip() for card in cards)
        if headings != HEADINGS:
            errors.append(f"{path.relative_to(ROOT)}: benefit heading order drifted")
        for index, card in enumerate(cards, 1):
            bullets = re.findall(r"<li>(.*?)</li>", card, re.S)
            if not 2 <= len(bullets) <= 3:
                errors.append(f"{path.relative_to(ROOT)}: benefit {index} has {len(bullets)} bullets")
            if words(card) > 55:
                errors.append(f"{path.relative_to(ROOT)}: benefit {index} is {words(card)} words; maximum 55")
        if not re.search(r'<span class="site-nav__context">(?:<span class="sr-only">Exam </span>)?', text):
            errors.append(f"{path.relative_to(ROOT)}: missing exam context pill")
        if "/section-nav.css" not in text or "/section-nav.js" not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing shared section navigation assets")

    content_pages = [ROOT / "index.html", ROOT / "guides/index.html", ROOT / "exams/index.html", ROOT / "exams/retired/index.html"]
    content_pages += sorted((ROOT / "guides").glob("*/index.html"))
    content_pages += [ROOT / "about/index.html", ROOT / "how-exam-iq-works/index.html", ROOT / "how-we-write-questions/index.html"]
    for path in content_pages:
        text = path.read_text()
        if "/section-nav.css" not in text or "/section-nav.js" not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing shared section navigation assets")
        if not re.search(r"fonts\.googleapis\.com/css2\?[^\"']*Outfit[^\"']*DM\+Sans", text):
            errors.append(f"{path.relative_to(ROOT)}: missing Outfit and DM Sans font bundle")
        for table in re.findall(r'<table class="[^"]*guide-table[^"]*".*?</table>', text, re.S):
            if "<td" in table and not re.search(r"<td[^>]+data-label=", table):
                errors.append(f"{path.relative_to(ROOT)}: guide table cells need mobile labels")

    for path in sorted((ROOT / "guides").glob("*/index.html")) + [ROOT / "about/index.html", ROOT / "how-exam-iq-works/index.html", ROOT / "how-we-write-questions/index.html", ROOT / "exams/retired/index.html"]:
        text = path.read_text()
        if '/article.css' not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing canonical article stylesheet")
        if re.search(r"\.guide-inline-cta\s*\{", text):
            errors.append(f"{path.relative_to(ROOT)}: duplicated inline CTA CSS")

    if errors:
        print("Marketing UI contract failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Marketing UI contract OK: {len(pages)} exam pages and {len(content_pages)} navigable content pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
