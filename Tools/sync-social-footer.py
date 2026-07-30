#!/usr/bin/env python3
"""Synchronise the shared Azure Mastery social-follow component across static pages."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PARTIAL = ROOT / "_includes" / "social-follow.html"
STYLE_LINK = '  <link rel="stylesheet" href="/social-follow.css">'
START_MARKER = "<!-- social-follow:start -->"
END_MARKER = "<!-- social-follow:end -->"


def target_pages() -> list[Path]:
    pages = [ROOT / "index.html", ROOT / "exams" / "_template.html"]
    pages.extend(sorted((ROOT / "exams").glob("*/index.html")))
    pages.append(ROOT / "guides" / "index.html")
    pages.extend(sorted((ROOT / "guides").glob("*/index.html")))
    pages.extend(
        ROOT / "apps" / "AzureMastery" / name
        for name in ("privacy.html", "terms.html", "support.html")
    )
    return pages


def indent_block(block: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else "" for line in block.strip().splitlines())


def remove_legacy_homepage_socials(text: str) -> str:
    text, nav_count = re.subn(
        r'\n      <nav class="footer-social" aria-label="Social media">.*?\n      </nav>',
        "",
        text,
        flags=re.S,
    )
    if nav_count not in (0, 1):
        raise ValueError(f"expected at most one legacy homepage social nav, found {nav_count}")

    text, css_count = re.subn(
        r"\n    \.footer-social \{.*?\n    \.footer-social svg \{ width: 16px; height: 16px; \}",
        "",
        text,
        flags=re.S,
    )
    if css_count not in (0, 1):
        raise ValueError(f"expected at most one legacy homepage social CSS block, found {css_count}")
    return text


def synchronise_page(page: Path, partial: str) -> str:
    text = page.read_text()
    if page == ROOT / "index.html":
        text = remove_legacy_homepage_socials(text)

    if STYLE_LINK not in text:
        if text.count("</head>") != 1:
            raise ValueError(f"{page.relative_to(ROOT)}: expected one closing head tag")
        text = text.replace("</head>", f"{STYLE_LINK}\n</head>", 1)

    marker_pattern = rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}"
    marker_matches = re.findall(marker_pattern, text, re.S)
    indented_partial = indent_block(partial)
    if len(marker_matches) == 1:
        return re.sub(marker_pattern, indented_partial.strip(), text, count=1, flags=re.S)
    if len(marker_matches) > 1:
        raise ValueError(f"{page.relative_to(ROOT)}: found multiple social-follow blocks")

    if '<footer class="site-footer">' in text:
        anchor = '  <footer class="site-footer">\n'
        if text.count(anchor) != 1:
            raise ValueError(f"{page.relative_to(ROOT)}: expected one site footer anchor")
        return text.replace(anchor, f"{anchor}{indented_partial}\n", 1)

    if page.name == "support.html":
        anchor = "\n    <hr>\n\n    <nav class=\"footer-nav\">"
        if text.count(anchor) != 1:
            raise ValueError("apps/AzureMastery/support.html: footer navigation anchor is missing")
        return text.replace(anchor, f"\n{indented_partial}\n{anchor}", 1)

    anchor = "\n  </div>\n</body>"
    if text.count(anchor) != 1:
        raise ValueError(f"{page.relative_to(ROOT)}: legal-page container anchor is missing")
    return text.replace(anchor, f"\n{indented_partial}\n  </div>\n</body>", 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing files")
    args = parser.parse_args()

    partial = PARTIAL.read_text().strip()
    if not partial.startswith(START_MARKER) or not partial.endswith(END_MARKER):
        sys.exit("social-follow partial must contain the canonical start and end markers")

    changed: list[Path] = []
    try:
        for page in target_pages():
            before = page.read_text()
            after = synchronise_page(page, partial)
            if after != before:
                changed.append(page)
                if not args.check:
                    page.write_text(after)
    except ValueError as exc:
        sys.exit(str(exc))

    if changed:
        verb = "would update" if args.check else "updated"
        print(f"{verb} {len(changed)} pages:")
        for page in changed:
            print(f"  {page.relative_to(ROOT)}")
        if args.check:
            sys.exit(1)
    else:
        print("Social-follow component is in sync across all target pages.")


if __name__ == "__main__":
    main()
