#!/usr/bin/env python3
"""Validate the static SEO contract for every Azure Mastery exam and guide page."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent


def _load_sitemap_lastmod_tool():
    """Load Tools/update-sitemap-lastmod.py, which owns sitemap <lastmod>.

    That tool's filename matches this repo's hyphenated Tools/ naming
    convention, so it can't be a plain `import`; load it by path instead so
    the validator checks against the exact same computation the tool
    writes, rather than duplicating the logic.
    """
    path = ROOT / "Tools" / "update-sitemap-lastmod.py"
    spec = importlib.util.spec_from_file_location("update_sitemap_lastmod", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    _sitemap_lastmod = _load_sitemap_lastmod_tool()
except subprocess.CalledProcessError:
    sys.exit("validate-marketing-seo: not inside a git checkout")
expected_lastmod = _sitemap_lastmod.expected_lastmod
loc_to_path = _sitemap_lastmod.loc_to_path
_COUNTS_DOC = json.loads((ROOT / "data" / "exam-counts.json").read_text())
COUNTS = _COUNTS_DOC["exams"]
# Which exams are current is decided in the app repo (any exam carrying a
# retirement date is classified non-current and drops to 0 exam-scoped
# questions) and mirrored into data/exam-counts.json by
# Tools/sync-marketing-counts.py, which owns every number on the site.
NON_CURRENT = set(_COUNTS_DOC.get("retired") or ())
SITABLE = {code for code in COUNTS if code not in NON_CURRENT}
RETIRED = {"AI-900": "30 June 2026", "AI-102": "30 June 2026", "DP-100": "1 June 2026",
           "AZ-204": "31 July 2026"}
RETIRING = {
    "AZ-500": ("31 August 2026", "SC-500"),
}
SUCCESSOR_ROUTES = {
    "AI-900": "AI-901",
    "AI-102": "AI-103",
    "DP-100": "AI-300",
    "AZ-204": "AI-200",
    **{code: successor for code, (_, successor) in RETIRING.items()},
}
# Every non-current exam must carry retirement page metadata, and nothing else
# may. RETIRED covers exams past their date, RETIRING those with one announced —
# together they have to equal the app's non-current set, or the two hand-kept
# dicts have drifted from the catalogue the way they did for AZ-204.
if set(RETIRED) | set(RETIRING) != NON_CURRENT:
    sys.exit(
        f"error: RETIRED+RETIRING in this file is {sorted(set(RETIRED) | set(RETIRING))} "
        f"but data/exam-counts.json says {sorted(NON_CURRENT)} are non-current. Update "
        f"RETIRED/RETIRING here and in Tools/optimise-marketing-seo.py, then re-run "
        f"Tools/optimise-marketing-seo.py."
    )

GUIDE_UPDATED = "2026-08-09"
GUIDE_UPDATED_LABEL = "Updated 9 August 2026"
GUIDE_SLUGS = (
    "which-azure-certification-first",
    "how-to-pass-az-900",
    "how-to-pass-az-104",
    "how-to-pass-sc-900",
    "how-to-pass-dp-900",
    "how-to-pass-ai-901",
    "az-900-vs-az-104",
    "sc-900-vs-az-900",
)
HOW_TO_GUIDE_SLUGS = {
    "how-to-pass-az-900",
    "how-to-pass-az-104",
    "how-to-pass-sc-900",
    "how-to-pass-dp-900",
    "how-to-pass-ai-901",
}
ACTIVE_SEO_REQUIREMENTS = {
    "AB-650": ("AI Services Administrator", "Copilot", "Purview"),
    "AI-500": ("Multi-Agent AI Solutions Expert", "Microsoft Foundry", "Agent Framework"),
    "AB-410": ("Intelligent Applications Builder", "Dataverse", "Power Apps"),
    "AZ-400": ("DevOps Engineer Expert", "Azure Pipelines", "GitHub Actions"),
    "AI-103": ("Developing AI Apps and Agents on Azure", "Microsoft Foundry"),
    "AB-620": ("Copilot Studio AI Agent Builder exam", "Power Platform"),
    "AI-901": ("current Azure AI Fundamentals exam", "Microsoft Foundry"),
    "PL-300": ("Power BI", "Power Query", "DAX"),
}
# Keep these templates in lockstep with optimise-marketing-seo.py's
# ACTIVE_SEO[code]["title"]; the count is substituted here from the same
# data/exam-counts.json snapshot so the two files cannot drift on the number.
_ACTIVE_SEO_TITLE_TEMPLATES = {
    "AI-901": "AI-901 Practice Questions — {count} Qs for AI Fundamentals (2026)",
    "AZ-400": "AZ-400 Practice Questions — {count} Qs for DevOps Engineer (2026)",
    "PL-300": "PL-300 Practice Questions — {count} Qs for Power BI Analyst (2026)",
}
ACTIVE_SEO_TITLES = {
    code: template.format(count=COUNTS[code])
    for code, template in _ACTIVE_SEO_TITLE_TEMPLATES.items()
}
TARGETED_STALE_PHRASES = {
    "AB-410": (
        "100-minute",
        "five domains",
        "April 2026 outline",
        "outline as published in <strong>August 2026</strong>",
        "40–60 multiple choice",
        "same formats Microsoft puts on the live exam",
        "mirroring Pearson VUE",
        "25–30 question online assessment",
        "Microsoft Fabric Data Agent",
    ),
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

MISLEADING_ALIGNMENT_PATTERNS = (
    ("real-exam question claim", r"\breal[- ]exam questions?\b"),
    ("real-exam simulation claim", r"\breal exam simulation\b"),
    ("exam mirroring claim", r"\bmirrors? (?:the )?(?:real|live|actual)(?: Microsoft)? exam\b"),
    ("exam-equivalence claim", r"\bmatches? (?:the )?(?:real|live|actual) exam\b"),
    ("exam-format equivalence claim", r"\bmatches? Microsoft(?:'s|’s) (?:real|live|actual) exam formats?\b"),
    ("same-as-live-format claim", r"\bsame formats? Microsoft puts on (?:the )?live exam\b"),
    ("Pearson VUE mirroring claim", r"\bmirroring Pearson VUE\b"),
    ("real bank-item claim", r"\ba real [A-Z]{2}-\d{3} (?:question-bank example|multi-select item|interactive-format prompt|prompt|case-study scenario)\b"),
    ("live-exam matching claim", r"\bmatching [^.]{0,120}\blive exam(?:'s|’s)?\b"),
    ("closest-to-live-exam claim", r"\bclosest you can get\b"),
    ("one-to-one claim", r"\b1:1\b"),
    ("unqualified currency claim", r"\bverified current\b"),
)

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

CERTIFICATION_CODES_BY_LEVEL = {
    "fundamentals": {
        "AB-900", "AI-900", "AI-901", "AZ-900", "DP-900", "PL-900", "SC-900",
    },
    "associate": {
        "AB-410", "AB-620", "AB-650", "AB-731", "AI-102", "AI-103", "AI-200",
        "AI-300", "AZ-104", "AZ-204", "AZ-500", "AZ-700", "DP-100", "DP-203",
        "DP-300", "DP-600", "DP-700", "DP-750", "DP-800", "PL-300", "SC-200",
        "SC-300", "SC-500",
    },
    "expert": {"AB-100", "AI-500", "AZ-305", "AZ-400", "SC-100"},
}
CERT_LEVEL_BY_CODE = {
    code: level
    for level, codes in CERTIFICATION_CODES_BY_LEVEL.items()
    for code in codes
}

SOCIAL_PROFILES = (
    ("instagram", "Instagram", "https://www.instagram.com/azuremastery.app"),
    ("x", "X", "https://x.com/AzureMastery"),
    ("tiktok", "TikTok", "https://www.tiktok.com/@azuremastery"),
    ("youtube", "YouTube", "https://www.youtube.com/channel/UCWhAwI2URaSg-5z2SQoaKYg"),
    ("facebook", "Facebook", "https://www.facebook.com/profile.php?id=61578421530035"),
)
SOCIAL_START_MARKER = "<!-- social-follow:start -->"
SOCIAL_END_MARKER = "<!-- social-follow:end -->"


def matches_once(pattern: str, text: str, label: str, page: Path, errors: list[str], flags: int = 0) -> str:
    found = re.findall(pattern, text, flags)
    if len(found) != 1:
        errors.append(f"{page.relative_to(ROOT)}: expected one {label}, found {len(found)}")
        return ""
    return found[0]


def normalise_visible_text(markup: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", "", markup)).split())


def social_target_pages() -> list[Path]:
    pages = [ROOT / "index.html", ROOT / "exams" / "_template.html"]
    pages.extend(ROOT / "exams" / code.lower() / "index.html" for code in sorted(COUNTS))
    pages.append(ROOT / "guides" / "index.html")
    pages.extend(ROOT / "guides" / slug / "index.html" for slug in GUIDE_SLUGS)
    pages.extend(
        ROOT / "apps" / "AzureMastery" / name
        for name in ("privacy.html", "terms.html", "support.html")
    )
    return pages


def validate_social_follow(errors: list[str]) -> None:
    partial = (ROOT / "_includes" / "social-follow.html").read_text().strip()
    marker_pattern = (
        rf"{re.escape(SOCIAL_START_MARKER)}.*?{re.escape(SOCIAL_END_MARKER)}"
    )

    for page in social_target_pages():
        text = page.read_text()
        if text.count('<link rel="stylesheet" href="/social-follow.css">') != 1:
            errors.append(f"{page.relative_to(ROOT)}: shared social-follow stylesheet is missing or duplicated")

        blocks = re.findall(marker_pattern, text, re.S)
        if len(blocks) != 1:
            errors.append(
                f"{page.relative_to(ROOT)}: expected one social-follow block, found {len(blocks)}"
            )
            continue

        block = blocks[0]
        normalised_block = re.sub(r"(?m)^ {4}", "", block).strip()
        if normalised_block != partial:
            errors.append(f"{page.relative_to(ROOT)}: social-follow block has drifted from the shared partial")

        if 'aria-label="Follow Azure Mastery on social media"' not in block:
            errors.append(f"{page.relative_to(ROOT)}: social navigation label is missing")
        for platform, label, url in SOCIAL_PROFILES:
            if block.count(url) != 1:
                errors.append(
                    f"{page.relative_to(ROOT)}: expected one {label} social link, found {block.count(url)}"
                )
            for marker in (
                f'data-social-platform="{platform}"',
                'data-social-placement="footer"',
                f'aria-label="Azure Mastery on {label}"',
                f"<span>{label}</span>",
            ):
                if marker not in block:
                    errors.append(f"{page.relative_to(ROOT)}: {label} social marker is missing: {marker}")

    homepage = (ROOT / "index.html").read_text()
    same_as_match = re.search(r'"sameAs": \[(.*?)\]', homepage, re.S)
    if not same_as_match:
        errors.append("homepage Organization sameAs list is missing")
    else:
        same_as = same_as_match.group(1)
        for _, label, url in SOCIAL_PROFILES:
            if same_as.count(url) != 1:
                errors.append(f"homepage Organization sameAs must contain one {label} profile")


def validate_sitemap_lastmod(errors: list[str], sitemap: str) -> None:
    """Every <url> in sitemap.xml must carry the <lastmod> that
    Tools/update-sitemap-lastmod.py computes for the page it points to
    (today's date if the file has uncommitted changes, otherwise its last
    commit date). That tool owns sitemap.xml's <lastmod> values -- run it,
    don't hand-edit them."""
    for block in re.findall(r"<url>.*?</url>", sitemap, re.S):
        loc_match = re.search(r"<loc>(.*?)</loc>", block)
        if not loc_match:
            continue
        loc = loc_match.group(1)
        expected = expected_lastmod(loc_to_path(loc))
        lastmod_match = re.search(r"<lastmod>(.*?)</lastmod>", block)
        current = lastmod_match.group(1) if lastmod_match else None
        if current != expected:
            current_label = current if current is not None else "missing"
            errors.append(
                f"sitemap entry for {loc} has lastmod {current_label!r}, expected {expected!r} "
                f"(run Tools/update-sitemap-lastmod.py)"
            )


def validate_guide_pages(errors: list[str], llms: str) -> list[Path]:
    guide_pages = [ROOT / "guides" / "index.html"]
    guide_pages.extend(ROOT / "guides" / slug / "index.html" for slug in GUIDE_SLUGS)

    expected_llms_contract = (
        "Every guide article includes FAQ structured data, and the five how-to guides "
        "also include study-plan structured data."
    )
    if expected_llms_contract not in llms:
        errors.append("llms.txt has a stale or inaccurate guide structured-data description")

    for page in guide_pages:
        slug = "" if page.parent == ROOT / "guides" else page.parent.name
        text = page.read_text()
        title = matches_once(r"<title>(.*?)</title>", text, "title", page, errors, re.S)
        description = matches_once(
            r'<meta name="description" content="([^"]*)">', text, "meta description", page, errors
        )
        canonical = matches_once(
            r'<link rel="canonical" href="([^"]+)">', text, "canonical", page, errors
        )
        expected_canonical = (
            "https://azuremastery.app/guides/"
            if not slug
            else f"https://azuremastery.app/guides/{slug}/"
        )
        if canonical != expected_canonical:
            errors.append(
                f"{page.relative_to(ROOT)}: canonical is {canonical}, expected {expected_canonical}"
            )
        if len(title) > 62:
            errors.append(f"{page.relative_to(ROOT)}: title is {len(title)} characters")
        if len(description) > 160:
            errors.append(f"{page.relative_to(ROOT)}: description is {len(description)} characters")

        matches_once(r"<h1\b[^>]*>.*?</h1>", text, "H1", page, errors, re.S)
        modified = matches_once(
            rf'<time datetime="([^"]+)">{re.escape(GUIDE_UPDATED_LABEL)}</time>',
            text,
            "semantic updated date",
            page,
            errors,
        )
        if modified and modified != GUIDE_UPDATED:
            errors.append(
                f"{page.relative_to(ROOT)}: visible updated date is {modified}, expected {GUIDE_UPDATED}"
            )

        required_markup = (
            '<meta name="robots" content="index, follow, max-image-preview:large, '
            'max-snippet:-1, max-video-preview:-1">',
            '<meta name="googlebot" content="index, follow, max-image-preview:large, max-snippet:-1">',
            '<meta name="author" content="Moonbeam Alpha Ltd">',
            '<meta name="publisher" content="Moonbeam Alpha Ltd">',
            '<link rel="alternate" type="application/llms.txt" href="/llms.txt">',
            'property="og:title"',
            'property="og:description"',
            'property="og:image"',
            'name="twitter:card"',
            'name="twitter:title"',
            'name="twitter:description"',
            'name="twitter:image"',
        )
        for marker in required_markup:
            if marker not in text:
                errors.append(f"{page.relative_to(ROOT)}: required SEO marker is missing: {marker}")

        og_url = matches_once(
            r'<meta property="og:url" content="([^"]+)">', text, "OpenGraph URL", page, errors
        )
        if og_url and og_url != expected_canonical:
            errors.append(
                f"{page.relative_to(ROOT)}: OpenGraph URL is {og_url}, expected {expected_canonical}"
            )

        schemas = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.S)
        graph: list[dict[str, object]] = []
        if len(schemas) != 1:
            errors.append(
                f"{page.relative_to(ROOT)}: expected one JSON-LD block, found {len(schemas)}"
            )
        else:
            try:
                payload = json.loads(schemas[0])
                graph = payload.get("@graph", [])
                if not isinstance(graph, list):
                    errors.append(f"{page.relative_to(ROOT)}: JSON-LD @graph is not a list")
                    graph = []
            except json.JSONDecodeError as exc:
                errors.append(f"{page.relative_to(ROOT)}: invalid JSON-LD: {exc}")

        schema_types = {
            item.get("@type") for item in graph if isinstance(item, dict) and item.get("@type")
        }
        required_types = {"WebPage", "BreadcrumbList", "ItemList"} if not slug else {
            "WebPage",
            "BreadcrumbList",
            "TechArticle",
            "FAQPage",
        }
        if slug in HOW_TO_GUIDE_SLUGS:
            required_types.add("HowTo")
        missing_types = required_types - schema_types
        if missing_types:
            errors.append(
                f"{page.relative_to(ROOT)}: missing JSON-LD types {sorted(missing_types)}"
            )
        if slug and slug not in HOW_TO_GUIDE_SLUGS and "HowTo" in schema_types:
            errors.append(
                f"{page.relative_to(ROOT)}: comparison or decision guide has misleading HowTo schema"
            )

        dated_nodes = [
            item for item in graph if isinstance(item, dict) and "dateModified" in item
        ]
        expected_dated_nodes = 1 if not slug else 2
        if len(dated_nodes) != expected_dated_nodes:
            errors.append(
                f"{page.relative_to(ROOT)}: expected {expected_dated_nodes} dated schema nodes, "
                f"found {len(dated_nodes)}"
            )
        for item in dated_nodes:
            if item["dateModified"] != GUIDE_UPDATED:
                errors.append(
                    f"{page.relative_to(ROOT)}: schema dateModified is {item['dateModified']}, "
                    f"expected {GUIDE_UPDATED}"
                )

        if slug:
            faq_nodes = [
                item for item in graph if isinstance(item, dict) and item.get("@type") == "FAQPage"
            ]
            visible_faqs = re.findall(
                r'<details class="faq">\s*<summary>(.*?)</summary>\s*'
                r'<div class="faq__answer"><p>(.*?)</p></div>\s*</details>',
                text,
                re.S,
            )
            if len(faq_nodes) != 1:
                errors.append(
                    f"{page.relative_to(ROOT)}: expected one FAQPage node, found {len(faq_nodes)}"
                )
            else:
                schema_faqs = faq_nodes[0].get("mainEntity", [])
                if len(schema_faqs) != len(visible_faqs):
                    errors.append(
                        f"{page.relative_to(ROOT)}: FAQ schema has {len(schema_faqs)} questions, "
                        f"visible section has {len(visible_faqs)}"
                    )
                else:
                    for position, (schema_faq, visible_faq) in enumerate(
                        zip(schema_faqs, visible_faqs), start=1
                    ):
                        schema_question = normalise_visible_text(str(schema_faq.get("name", "")))
                        schema_answer = normalise_visible_text(
                            str(schema_faq.get("acceptedAnswer", {}).get("text", ""))
                        )
                        visible_question = normalise_visible_text(visible_faq[0])
                        visible_answer = normalise_visible_text(visible_faq[1])
                        if (schema_question, schema_answer) != (visible_question, visible_answer):
                            errors.append(
                                f"{page.relative_to(ROOT)}: FAQ {position} schema does not match visible text"
                            )
            if "https://learn.microsoft.com/" not in text:
                errors.append(
                    f"{page.relative_to(ROOT)}: official Microsoft Learn source link is missing"
                )

        if canonical and canonical not in llms:
            errors.append(f"{page.relative_to(ROOT)}: canonical URL is missing from llms.txt")

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

    robots = (ROOT / "robots.txt").read_text()
    for crawler in (
        "OAI-SearchBot",
        "ChatGPT-User",
        "ClaudeBot",
        "PerplexityBot",
        "Google-Extended",
    ):
        if not re.search(
            rf"User-agent: {re.escape(crawler)}\s+Allow: /",
            robots,
        ):
            errors.append(f"robots.txt does not explicitly allow {crawler}")

    return guide_pages


def main() -> None:
    errors: list[str] = []

    for script in (
        ROOT / "Tools" / "optimise-marketing-seo.py",
        ROOT / "Tools" / "sync-marketing-counts.py",
        ROOT / "Tools" / "sync-social-footer.py",
    ):
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
        expected_title = ACTIVE_SEO_TITLES.get(code)
        if expected_title is not None and title != expected_title:
            errors.append(f"{page.relative_to(ROOT)}: tailored {code} title is missing")
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
        expected_count_phrase = f"{count} {code} practice questions"
        if expected_count_phrase not in text:
            errors.append(
                f"{page.relative_to(ROOT)}: scoped practice-question count is not {count}"
            )
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

        certification_chips = re.findall(
            r'(<(?:a|span)\s+class="[^"]*cert-path__chip(?:\s|")[^>]*>)\s*'
            r'<span class="cert-path__chip-code">([A-Z]{2,3}-\d{3})</span>',
            text,
            re.S,
        )
        for opening_tag, certification_code in certification_chips:
            expected_level = CERT_LEVEL_BY_CODE.get(certification_code)
            if expected_level is None:
                errors.append(
                    f"{page.relative_to(ROOT)}: certification tier is unmapped for {certification_code}"
                )
                continue
            level_match = re.search(r'data-cert-level="([^"]+)"', opening_tag)
            actual_level = level_match.group(1) if level_match else None
            if actual_level != expected_level:
                errors.append(
                    f"{page.relative_to(ROOT)}: {certification_code} tier is {actual_level!r}, "
                    f"expected {expected_level!r}"
                )

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
        # "full 319-question bank" / "full 320-question bank" used to live here as
        # stale-count guards. Tools/sync-marketing-counts.py now owns that phrase
        # and rewrites it per page, so --check catches any drift, while a bare
        # number literal false-positives the moment a real count reaches it —
        # AI-300 is legitimately 319 exam-scoped questions.
    )
    for phrase in stale_phrases:
        if phrase in corpus:
            errors.append(f"stale or generic content remains: {phrase}")

    truthfulness_surfaces = corpus + "\n" + (ROOT / "index.html").read_text()
    truthfulness_surfaces += "\n" + (ROOT / "exams" / "_template.html").read_text()
    for label, pattern in MISLEADING_ALIGNMENT_PATTERNS:
        if re.search(pattern, normalise_visible_text(truthfulness_surfaces), re.I):
            errors.append(f"misleading exam-alignment copy remains: {label}")

    llms = (ROOT / "llms.txt").read_text()
    if f"## Exams covered ({len(SITABLE)})" not in llms:
        errors.append("llms.txt has a stale exam-count heading")
    for match in re.finditer(
        r"^### (?P<label>[^\n]+?) \((?P<declared>\d+)\)\n(?P<body>.*?)(?=^### |^## |\Z)",
        llms,
        re.M | re.S,
    ):
        # Retired and retiring exams keep their bullets as a reference, but the
        # heading counts only what still feeds the advertised totals.
        bulleted = re.findall(r"^-\s+\[?([A-Z]{2}-\d{3})\b", match.group("body"), re.M)
        actual = sum(1 for code in bulleted if code not in NON_CURRENT)
        declared = int(match.group("declared"))
        if actual != declared:
            errors.append(
                f"llms.txt category {match.group('label')!r} declares {declared} "
                f"but lists {actual} sit-able exam(s)"
            )
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
    validate_sitemap_lastmod(errors, sitemap)

    guide_pages = validate_guide_pages(errors, llms)
    validate_social_follow(errors)

    if errors:
        print(f"SEO validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    print(
        f"SEO validation passed for {len(pages)} exam pages "
        f"and {len(guide_pages)} guide pages."
    )


if __name__ == "__main__":
    main()
