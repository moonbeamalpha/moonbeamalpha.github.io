#!/usr/bin/env python3
"""Generate llms-full.txt — the expanded machine-readable site summary.

Starts from llms.txt verbatim, then appends, per exam page, the content an AI
assistant most often needs to answer a user's question in one fetch:

  - the page's dateModified (from its WebPage JSON-LD)
  - the credential's domain list with weights (EducationalOccupationalCredential)
  - every FAQ question and full answer (FAQPage)

Everything is extracted from the pages' own JSON-LD, so this file can never
disagree with the site: re-run after any exam-page change.

    python3 Tools/generate-llms-full.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def jsonld_blocks(html: str):
    for m in re.finditer(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S):
        try:
            yield json.loads(m.group(1))
        except json.JSONDecodeError:
            continue


def nodes_of_type(html: str, typ: str):
    for block in jsonld_blocks(html):
        graph = block.get("@graph", [block])
        for node in graph:
            if node.get("@type") == typ:
                yield node


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    base = open(os.path.join(ROOT, "llms.txt")).read().rstrip("\n")
    out = [base, "", "", "# Full detail per exam page", "",
           "Everything below is extracted from each page's own structured data "
           "(FAQPage, EducationalOccupationalCredential, WebPage) and regenerated "
           "whenever a page changes, so it always matches the live site.", ""]

    pages = sorted(glob.glob(os.path.join(ROOT, "exams", "*", "index.html")))
    n_faq = 0
    for path in pages:
        slug = os.path.basename(os.path.dirname(path))
        html = open(path).read()
        title = re.search(r"<title>(.*?)</title>", html)
        out.append(f"## /exams/{slug}/ — {clean(title.group(1)) if title else slug}")

        for node in nodes_of_type(html, "WebPage"):
            mod = node.get("dateModified")
            if mod:
                out.append(f"Page last modified: {mod}")
            break

        for node in nodes_of_type(html, "EducationalOccupationalCredential"):
            comps = node.get("competencyRequired", [])
            if comps:
                out.append("Exam domains:")
                for c in comps:
                    name = c.get("name", "") if isinstance(c, dict) else str(c)
                    out.append(f"  - {clean(name)}")
            break

        for node in nodes_of_type(html, "FAQPage"):
            for q in node.get("mainEntity", []):
                out.append(f"Q: {clean(q.get('name', ''))}")
                out.append(f"A: {clean(q.get('acceptedAnswer', {}).get('text', ''))}")
                n_faq += 1
            break
        out.append("")

    dest = os.path.join(ROOT, "llms-full.txt")
    with open(dest, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote llms-full.txt: {len(pages)} exam pages, {n_faq} FAQ pairs, "
          f"{os.path.getsize(dest):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
