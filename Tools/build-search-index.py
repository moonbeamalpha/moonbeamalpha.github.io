#!/usr/bin/env python3
"""Generate public search data; --check validates without writing. No app checkout needed."""
from __future__ import annotations

import argparse
import ast
import gzip
import json
import re
import sys
from search_common import ROOT, Document, clean, content_root, excluded, published_pages

OUTPUT = ROOT / 'data/search-index.json'
FEATURES = {
    'ask-aura': 'Ask Aura — private study companion',
    'exam-iq': 'Exam IQ — predicted exam score',
    'features': 'Azure Mastery study features',
    'exam-simulator': 'Exam simulator and certification paths',
    'devices': 'Azure Mastery on iPhone, iPad, Mac and Apple Watch',
    'screenshots': 'Azure Mastery screenshots',
    'faq': 'Azure Mastery frequently asked questions',
}
FAMILIES = {'AZ': 'Azure', 'AI': 'AI & Agents', 'AB': 'AI & Agents',
            'DP': 'Data', 'PL': 'Data', 'SC': 'Security', 'GH': 'GitHub'}
SUBJECTS = {
    'Networking': r'\bnetwork(?:ing|s)?\b', 'Identity': r'\b(?:identity|entra)\b',
    'Microsoft 365': r'\b(?:microsoft 365|m365)\b', 'Copilot': r'\bcopilot\b',
    'Power BI': r'\bpower bi\b', 'Power Platform': r'\bpower (?:platform|apps|automate)\b',
    'Fabric': r'\bfabric\b', 'Databricks': r'\bdatabricks\b',
    'Machine learning': r'\b(?:machine learning|mlops)\b', 'DevOps': r'\bdevops\b',
    'Security': r'\bsecurity\b', 'AI & Agents': r'\b(?:artificial intelligence|agents|generative ai)\b',
}


def lifecycle_data():
    source = ast.parse((ROOT / 'Tools/optimise-marketing-seo.py').read_text())
    return {target.id: ast.literal_eval(node.value) for node in source.body
            if isinstance(node, ast.Assign) for target in node.targets
            if isinstance(target, ast.Name) and target.id in {'RETIRED_EXAMS', 'RETIRING_EXAMS'}}


def build_index(root=ROOT):
    snapshot = json.loads((root / 'data/exam-counts.json').read_text())
    lifecycle = lifecycle_data()
    retired = lifecycle['RETIRED_EXAMS']
    retiring = lifecycle['RETIRING_EXAMS']
    if set(retired) | set(retiring) != set(snapshot['retired']):
        raise ValueError('Search retirement metadata disagrees with the catalogue snapshot')
    entries = []
    for url, file in published_pages(root):
        document = Document(file.read_text()).root
        body = content_root(document)
        if not body:
            raise ValueError(f'{url}: missing content')
        title_node = document.find(lambda n: n.tag == 'h1') or document.find(lambda n: n.tag == 'title')
        title = clean(title_node.text())
        description = document.find(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'description')
        summary = clean(description.attrs.get('content', '')) if description else title
        text = clean(body.text(excluded))
        headings = [clean(n.text(excluded)) for n in body.all(lambda n: n.tag in {'h1', 'h2', 'h3'}, excluded)
                    if clean(n.text(excluded))]
        match = re.fullmatch(r'/exams/([a-z]{2}-\d{3})/', url)
        code = match[1].upper() if match else None
        kind = 'exam' if code else 'guide' if url.startswith('/guides/') and url != '/guides/' else 'page'
        codes = [code] if code else sorted(set(re.findall(r'\b(?:AZ|AI|AB|DP|PL|SC|GH)-\d{3}\b', title)))
        subjects = sorted({FAMILIES[c[:2]] for c in codes if c[:2] in FAMILIES}
                          | {label for label, pattern in SUBJECTS.items()
                             if re.search(pattern, ' '.join([title, summary, *headings]), re.I)})
        status = 'retiring' if code in retiring else 'retired' if code in retired else 'current'
        meta = retiring.get(code) or retired.get(code) or {}
        if code:
            title = f'{code} — {snapshot["names"][code]}'
            if status != 'current':
                summary = f'{code} is {status}. Use this reference page to compare the final outline and the current successor.'
        entry = dict(url=url, title=title, kind=kind, summary=summary, text=text,
                     headings=' '.join(headings), examCodes=codes, subjects=subjects, status=status)
        if code in snapshot['retirement_dates']:
            entry['retirementDate'] = snapshot['retirement_dates'][code]
        if meta.get('replacement'):
            successor = meta['replacement']
            entry['successor'] = {'code': successor, 'url': f'/exams/{successor.lower()}/'}
        entries.append(entry)
        if url == '/':
            for anchor, label in FEATURES.items():
                section = document.find(lambda n: n.attrs.get('id') == anchor)
                if not section:
                    raise ValueError(f'Missing homepage search feature #{anchor}')
                feature_text = clean(section.text(excluded))
                paragraphs = [clean(n.text(excluded)) for n in section.all(lambda n: n.tag == 'p', excluded)]
                # Prefer explanatory copy over short eyebrow labels such as "Frequently asked".
                feature_summary = next((paragraph for paragraph in paragraphs if len(paragraph) >= 50),
                                       feature_text[:180])
                entries.append(dict(url=f'/#{anchor}', title=label, kind='page',
                                    summary=feature_summary,
                                    text=feature_text, headings=label, examCodes=[], subjects=[], status='current'))
    return {'version': 1, 'entries': sorted(entries, key=lambda e: e['url'])}


def rendered_index(root=ROOT):
    return json.dumps(build_index(root), ensure_ascii=False, separators=(',', ':'), sort_keys=True) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = rendered_index()
    compressed = len(gzip.compress(expected.encode(), mtime=0))
    if compressed > 150 * 1024:
        raise ValueError(f'Search index exceeds 150 KiB gzip: {compressed} bytes')
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != expected:
            print('Search index is stale; run python3 Tools/build-search-index.py', file=sys.stderr)
            return 1
    else:
        OUTPUT.write_text(expected)
    print(f'Search index {"OK" if args.check else "generated"}: {len(json.loads(expected)["entries"])} destinations, '
          f'{compressed:,} bytes gzip')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
