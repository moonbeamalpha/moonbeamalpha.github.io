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
RETIRING = {
    "AZ-204": ("31 July 2026", "AI-200"),
    "AZ-500": ("31 August 2026", "SC-500"),
}
SUCCESSOR_ROUTES = {
    "AI-900": "AI-901",
    "AI-102": "AI-103",
    "DP-100": "AI-300",
    **{code: successor for code, (_, successor) in RETIRING.items()},
}
SEO_UPDATED = "2026-07-25"
SEO_UPDATED_OVERRIDES = {}
ACTIVE_SEO_REQUIREMENTS = {
    "AI-103": ("Developing AI Apps and Agents on Azure", "Microsoft Foundry"),
    "AB-620": ("Copilot Studio AI Agent Builder exam", "Power Platform"),
    "AI-901": ("current Azure AI Fundamentals exam", "Microsoft Foundry"),
}
TARGETED_STALE_PHRASES = {
    "AI-103": (
        "AI-900 first if AI concepts are new to you",
        "AI-900 builds the AI vocabulary",
        "AI-103 vs AI-900 — which should I take first?",
    ),
    "AB-620": (
        "five AB-620 domains",
        "the exam expects you to know specific PowerShell and Azure CLI commands",
        "AI-900 builds the AI vocabulary",
        "AB-620 vs AI-900 — which should I take first?",
    ),
    "AI-901": (
        "Sister fundamentals exam — same skills outline",
        "Pick whichever has the question style that suits you",
    ),
    "AZ-204": (
        "remains renewable even after the AZ-204 exam retires",
        "Both expect the developer-side experience AZ-204 validates",
    ),
    "AZ-305": (
        "AZ-204 works as well",
        "Alternative Associate prerequisite",
        "Associate prereq (alt)",
    ),
    "AZ-400": (
        "They share AZ-104/AZ-204 as the Associate prerequisite",
        "first-time pass rate is meaningfully lower",
    ),
    "SC-100": (
        "or MS-500 also satisfy the requirement",
        "AZ-500, SC-200, SC-300, or MS-500",
    ),
    "SC-500": (
        '<span class="cert-path__chip-role">prereq option</span>',
        "feeds into the SC-100 Cybersecurity Architect Expert credential",
    ),
}

ACTIVE_PAGES_WITHOUT_RETIRED_ROUTES = {
    "AB-100",
    "AB-620",
    "AB-731",
    "AB-900",
    "AI-200",
    "DP-300",
    "DP-800",
    "DP-900",
    "GH-300",
    "GH-900",
    "PL-300",
    "PL-900",
    "SC-900",
}


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
        smart_banner = matches_once(
            r'<meta name="apple-itunes-app" content="([^"]+)">',
            text,
            "Smart App Banner",
            page,
            errors,
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
        for phrase in ACTIVE_SEO_REQUIREMENTS.get(code, ()):
            if phrase not in description:
                errors.append(f"{page.relative_to(ROOT)}: tailored description is missing {phrase!r}")
        if code == "AI-901" and title != "AI-901 Practice Questions | Azure AI Fundamentals Exam":
            errors.append(f"{page.relative_to(ROOT)}: tailored AI-901 title is missing")
        for phrase in TARGETED_STALE_PHRASES.get(code, ()):
            if phrase in text:
                errors.append(f"{page.relative_to(ROOT)}: stale targeted copy remains: {phrase}")
        if "the exam expects you to know specific PowerShell and Azure CLI commands" in text:
            errors.append(f"{page.relative_to(ROOT)}: generic command-study advice remains")
        if code in ACTIVE_PAGES_WITHOUT_RETIRED_ROUTES:
            route_sections = "\n".join(
                re.findall(
                    r'<section id="(?:cert-paths|related)".*?</section>',
                    text,
                    re.S,
                )
            )
            for retired_code in RETIRED:
                retired_href = f'href="/exams/{retired_code.lower()}/"'
                if retired_href in route_sections:
                    errors.append(
                        f"{page.relative_to(ROOT)}: active pathway still links to retired {retired_code}"
                    )
        expected_canonical = f"https://azuremastery.app/exams/{code.lower()}/"
        if canonical != expected_canonical:
            errors.append(f"{page.relative_to(ROOT)}: canonical is {canonical}, expected {expected_canonical}")
        expected_banner = (
            f"app-id=6760594569, app-argument=azuremastery://exam/{code.lower()}"
        )
        if smart_banner != expected_banner:
            errors.append(
                f"{page.relative_to(ROOT)}: Smart App Banner is {smart_banner}, expected {expected_banner}"
            )
        if code not in {"GH-300", "GH-900"} and f"full {count}-question bank" not in text:
            errors.append(f"{page.relative_to(ROOT)}: full-bank count is not {count}")
        if code in RETIRED and ("Retired Exam" not in title or RETIRED[code] not in description):
            errors.append(f"{page.relative_to(ROOT)}: retired-exam metadata is missing")
        if code in RETIRING:
            retirement_date, successor = RETIRING[code]
            if successor not in title or retirement_date not in description:
                errors.append(f"{page.relative_to(ROOT)}: retiring-exam metadata is missing")
        if code in SUCCESSOR_ROUTES:
            successor = SUCCESSOR_ROUTES[code]
            if f'href="/exams/{successor.lower()}/"' not in text:
                errors.append(f"{page.relative_to(ROOT)}: successor route to {successor} is missing")
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
        expected_lastmod = SEO_UPDATED_OVERRIDES.get(code, SEO_UPDATED)
        if not block or f"<lastmod>{expected_lastmod}</lastmod>" not in block.group(0):
            errors.append(f"sitemap entry missing or stale for {code}")

    if errors:
        print(f"SEO validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    print(f"SEO validation passed for {len(pages)} exam pages.")


if __name__ == "__main__":
    main()
