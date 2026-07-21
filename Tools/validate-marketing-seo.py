#!/usr/bin/env python3
"""Validate the static SEO contract for every Azure Mastery exam page."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
COUNTS = json.loads((ROOT / "data" / "exam-counts.json").read_text())["exams"]
RETIRED = {"AI-900": "30 June 2026", "AI-102": "30 June 2026", "DP-100": "1 June 2026"}


def matches_once(pattern: str, text: str, label: str, page: Path, errors: list[str], flags: int = 0) -> str:
    found = re.findall(pattern, text, flags)
    if len(found) != 1:
        errors.append(f"{page.relative_to(ROOT)}: expected one {label}, found {len(found)}")
        return ""
    return found[0]


def main() -> None:
    errors: list[str] = []

    for script in (ROOT / "Tools" / "optimise-marketing-seo.py", ROOT / "Tools" / "sync-marketing-counts.py"):
        try:
            ast.parse(script.read_text(), filename=str(script))
        except SyntaxError as exc:
            errors.append(str(exc))

    pages = [ROOT / "exams" / code.lower() / "index.html" for code in sorted(COUNTS)]
    for code, page in zip(sorted(COUNTS), pages):
        count = COUNTS[code]
        text = page.read_text()
        title = matches_once(r"<title>(.*?)</title>", text, "title", page, errors, re.S)
        description = matches_once(
            r'<meta name="description" content="([^"]*)">', text, "meta description", page, errors
        )
        canonical = matches_once(
            r'<link rel="canonical" href="([^"]+)">', text, "canonical", page, errors
        )
        matches_once(r"<h1\b[^>]*>.*?</h1>", text, "H1", page, errors, re.S)

        schemas = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.S)
        if len(schemas) != 1:
            errors.append(f"{page.relative_to(ROOT)}: expected one JSON-LD block, found {len(schemas)}")
        else:
            try:
                json.loads(schemas[0])
            except json.JSONDecodeError as exc:
                errors.append(f"{page.relative_to(ROOT)}: invalid JSON-LD: {exc}")

        if len(title) > 62:
            errors.append(f"{page.relative_to(ROOT)}: title is {len(title)} characters")
        if len(description) > 160:
            errors.append(f"{page.relative_to(ROOT)}: description is {len(description)} characters")
        expected_canonical = f"https://azuremastery.app/exams/{code.lower()}/"
        if canonical != expected_canonical:
            errors.append(f"{page.relative_to(ROOT)}: canonical is {canonical}, expected {expected_canonical}")
        if code not in {"GH-300", "GH-900"} and f"full {count}-question bank" not in text:
            errors.append(f"{page.relative_to(ROOT)}: full-bank count is not {count}")
        if code in RETIRED and ("Retired Exam" not in title or RETIRED[code] not in description):
            errors.append(f"{page.relative_to(ROOT)}: retired-exam metadata is missing")
        if "Answer Coach" not in text:
            errors.append(f"{page.relative_to(ROOT)}: Answer Coach product naming is missing")
        if re.search(r"Why Wrong|Why Was I Wrong", text, re.I):
            errors.append(f"{page.relative_to(ROOT)}: stale pre-v1.9 coaching name remains")
        if "generated on-device by Apple Foundation Model" in text:
            errors.append(f"{page.relative_to(ROOT)}: stale Answer Coach provenance remains")

        ids = set(re.findall(r'\bid="([^"]+)"', text))
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith("#"):
                if href[1:] and href[1:] not in ids:
                    errors.append(f"{page.relative_to(ROOT)}: missing fragment target {href}")
                continue
            if href.startswith(("http:", "https:", "mailto:", "tel:")):
                continue
            url = urlsplit(href)
            target = ROOT / url.path.lstrip("/") if href.startswith("/") else page.parent / url.path
            if url.path.endswith("/"):
                target /= "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(ROOT)}: missing internal target {href}")

    corpus = "\n".join(page.read_text() for page in pages)
    stale_phrases = (
        "Which Azure compute service is best for event-driven container workloads?",
        "Order the steps to deploy a Bicep template.",
        "Azure sysadmin, Microsoft certification",
        "Bicep, ARM templates, Azure RBAC, NSG, Azure Backup",
        "full 319-question bank",
        "full 320-question bank",
    )
    for phrase in stale_phrases:
        if phrase in corpus:
            errors.append(f"stale or generic content remains: {phrase}")

    llms = (ROOT / "llms.txt").read_text()
    if "## Exams covered (32)" not in llms:
        errors.append("llms.txt has a stale exam-count heading")
    if "Platform: iOS 18+, iPadOS 18+" not in llms:
        errors.append("llms.txt has a stale minimum OS version")
    if "Answer Coach" not in llms or re.search(r"Why Wrong|Why Was I Wrong", llms, re.I):
        errors.append("llms.txt has stale Answer Coach naming")

    homepage = (ROOT / "index.html").read_text()
    if "Answer Coach" not in homepage or re.search(r"Why Wrong|Why Was I Wrong", homepage, re.I):
        errors.append("homepage has stale Answer Coach naming")
    if "generated by Apple's Foundation Model" in homepage:
        errors.append("homepage has stale Answer Coach provenance")

    sitemap = (ROOT / "sitemap.xml").read_text()
    for code in COUNTS:
        block = re.search(
            rf"<url>\s*<loc>https://azuremastery\.app/exams/{re.escape(code.lower())}/</loc>.*?</url>",
            sitemap,
            re.S,
        )
        if not block or "<lastmod>2026-07-21</lastmod>" not in block.group(0):
            errors.append(f"sitemap entry missing or stale for {code}")

    if errors:
        print(f"SEO validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    print(f"SEO validation passed for {len(pages)} exam pages.")


if __name__ == "__main__":
    main()
