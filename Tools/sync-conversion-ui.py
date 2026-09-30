#!/usr/bin/env python3
"""Synchronise static conversion UI, catalogue-derived exam cards and placement links."""
from __future__ import annotations
import argparse
import html
import hashlib
import json
import re
from search_common import ROOT, Document, Node, clean, published_pages

STORE = 'https://apps.apple.com/app/id6760594569'
PROVIDER = '128558698'
LABELS = {'infra': 'Azure infrastructure', 'data-ai': 'Data & AI', 'devops': 'Apps & DevOps',
          'business': 'Business & Copilot', 'security': 'Security', 'github': 'GitHub'}
FEATURED = ['AZ-900', 'AZ-104', 'AI-901', 'DP-700', 'PL-300', 'SC-900']
EXAM_HERO_CHROME = ('<a class="conversion-try" href="#question-types">Try a practice question →</a>\n'
                   '<p class="conversion-terms">Free starter questions · No account needed.<br>'
                   'Full banks: one-time purchase. Pro adds every bank and advanced study tools. '
                   '<a href="/#pricing">Compare access options</a>.</p>\n'
                   '<p class="conversion-proof">Original questions with written explanations. '
                   '<a href="/how-we-write-questions/">How we review them</a> · '
                   '<a href="/how-exam-iq-works/">About readiness estimates</a></p>')


def short_campaign(value):
    return value if len(value) <= 30 else value[:23] + '-' + hashlib.sha256(value.encode()).hexdigest()[:6]


def block(text, name, content, anchor):
    expected = f'<!-- conversion-{name}:start -->\n{content}\n<!-- conversion-{name}:end -->'
    pattern = rf'<!-- conversion-{name}:start -->.*?<!-- conversion-{name}:end -->'
    if re.search(pattern, text, re.S):
        return re.sub(pattern, lambda _: expected, text, count=1, flags=re.S)
    if text.count(anchor) != 1:
        raise ValueError(f'{name}: missing or ambiguous anchor {anchor}')
    return text.replace(anchor, expected + '\n' + anchor, 1)


def exam_metadata(home):
    grid = Document(home).root.find(lambda n: 'roadmap-grid' in n.attrs.get('class', '').split())
    if not grid:
        raise ValueError('Missing authored roadmap classification')
    metadata = {}
    level = None
    for node in grid.children:
        if not isinstance(node, Node):
            continue
        if 'roadmap-level' in node.attrs.get('class', '').split():
            level = clean(node.text())
        if level and 'roadmap-cell' in node.attrs.get('class', '').split():
            for link in node.all(lambda n: n.tag == 'a'):
                code = clean(link.text())
                metadata[code] = (level, node.attrs['data-category'])
    return metadata


def finder_cards(snapshot, metadata):
    current = sorted(set(snapshot['exams']) - set(snapshot['retired']))
    if set(current) - set(metadata):
        raise ValueError('Current exams missing roadmap classification: ' + str(set(current) - set(metadata)))
    def card(code):
        level, category = metadata[code]
        name = snapshot['names'][code]
        if 'Fundamentals' in name or 'Foundations' in name:
            level = 'Fundamentals'
        # The title already conveys the level for names such as Power BI Data Analyst Associate.
        meta = LABELS[category] if level.lower() in name.lower() else f'{level} · {LABELS[category]}'
        return (f'<a class="exam-finder__card exam-mini__tag" data-exam-category="{category}" href="/exams/{code.lower()}/">'
                f'<span class="exam-finder__code">{code}<span aria-hidden="true">↗</span></span>'
                f'<span class="exam-finder__title">{html.escape(name.removeprefix("Microsoft "))}</span>'
                f'<span class="exam-finder__meta">{meta}</span></a>')
    featured = [code for code in FEATURED if code in current]
    return ('<div class="exam-finder__grid">' + '\n'.join(card(code) for code in featured) + '</div>\n'
            '<details class="exam-finder__more"><summary>Browse every current exam</summary><div class="exam-finder__grid">' +
            '\n'.join(card(code) for code in current if code not in featured) + '</div></details>')


def campaign_links(text, relative):
    """Static attribution works without JS; an explicit placement token always wins."""
    from urllib.parse import urlsplit, parse_qsl, urlencode
    stem = ('site-home' if relative == 'index.html' else 'exam-index' if relative == 'exams/index.html'
            else 'guide-index' if relative == 'guides/index.html'
            else relative.removesuffix('/index.html').removesuffix('.html').replace('exams/', 'exam-').replace('guides/', 'guide-').replace('/', '-'))
    stem = 'exam-{{CERT_CODE_LOWER}}' if relative == 'exams/_template.html' else stem[:32]
    def replace(match):
        tag = match[0]
        found = re.search(r'href="([^\"]+)"', tag)
        if not found:
            return tag
        url = urlsplit(html.unescape(found[1]))
        if url.hostname != 'apps.apple.com' or 'id6760594569' not in url.path:
            return tag
        params = dict(parse_qsl(url.query))
        classes = re.search(r'class="([^\"]*)"', tag)
        classes = classes[1] if classes else ''
        placement = ('nav' if 'nav' in classes else 'hero' if any(c in classes for c in ['btn-primary', 'hero__cta'])
                     else 'footer' if any(c in classes for c in ['app-store-badge', 'cta-final']) else None)
        prefix = text[:match.start()]
        section = prefix[prefix.rfind('<section'):]
        if 'class="cta-final"' in section and 'cta-button' in classes:
            placement = 'footer'
        if 'id="pricing"' in section and 'btn-primary' in classes:
            placement = 'free-starter'
        if relative == 'exams/_template.html' and 'mobile-cta-bar__btn' in classes:
            params['ct'] = stem + '-sticky'
        if placement:
            params['ct'] = stem + '-' + placement
        elif not params.get('ct'):
            params['ct'] = stem + '-body'
        params['pt'] = PROVIDER; params['mt'] = '8'
        if relative != 'exams/_template.html':
            params['ct'] = short_campaign(params['ct'])
        encoded = urlencode(params).replace('%7B', '{').replace('%7D', '}') if relative == 'exams/_template.html' else urlencode(params)
        return tag.replace(found[0], 'href="' + STORE + '?' + html.escape(encoded, quote=True) + '"')
    text = re.sub(r'<a\b[^>]*>', replace, text)
    def banner(match):
        content = html.unescape(match[1])
        content = re.sub(r',\s*affiliate-data=[^,]*', '', content)
        campaign = stem + '-banner'
        if relative != 'exams/_template.html': campaign = short_campaign(campaign)
        content += ', affiliate-data=pt=' + PROVIDER + '&ct=' + campaign + '&mt=8'
        return '<meta name="apple-itunes-app" content="' + html.escape(content, quote=True) + '">'
    return re.sub(r'<meta name="apple-itunes-app" content="([^\"]*)">', banner, text)


def render(path, text, snapshot, metadata):
    relative = path.relative_to(ROOT).as_posix()
    assets = '<link rel="stylesheet" href="/conversion.css">\n<script src="/conversion.js" defer></script>'
    is_exam = re.fullmatch(r'exams/[a-z]{2}-\d{3}/index.html', relative) or relative == 'exams/_template.html'
    if relative == 'index.html' or is_exam:
        assets += '\n<script src="/practice.js" defer></script>'
    for asset in ['/conversion.css', '/conversion.js', '/practice.js']:
        versioned = re.search(re.escape(asset) + r'\?v=[0-9a-f]{12}', text)
        if versioned:
            assets = assets.replace('"' + asset + '"', '"' + versioned[0] + '"')
    text = block(text, 'assets', assets, '</head>')
    if relative == 'index.html':
        text = block(text, 'cards', finder_cards(snapshot, metadata), '<!-- exam-roadmap-map:start -->')
    if is_exam:
        text = block(text, 'hero', EXAM_HERO_CHROME, '          <div class="am-cert-hero__ctas">')
        # Bring the useful interaction into the decision path without deleting reference material.
        sample = re.search(r'    <section id="question-types".*?</section>', text, re.S)
        hero = re.search(r'<section\b[^>]*class="am-cert-hero".*?</section>', text, re.S)
        if sample and hero and sample.start() > hero.end() + 20:
            content = sample[0]
            text = text[:sample.start()] + text[sample.end():]
            hero = re.search(r'<section\b[^>]*class="am-cert-hero".*?</section>', text, re.S)
            text = text[:hero.end()] + '\n\n' + content + text[hero.end():]
    if relative == 'exams/index.html':
        text = text.replace('<main>', '<main data-exam-finder>')
        filters = ('<div class="exam-finder__filters" data-exam-filters hidden role="group" aria-label="Filter exams by subject">' +
                   ''.join(f'<button type="button" data-exam-filter="{key}" aria-pressed="{str(key == "all").lower()}">{label}</button>'
                           for key, label in [('all', 'All'), *LABELS.items()]) + '</div>'
                   '<p class="exam-finder__count" data-exam-count role="status" aria-live="polite"></p>')
        filters = '<div class="container exam-finder__controls">' + filters + '</div>'
        text = block(text, 'hub-filters', filters, '<section id="fam-azure"')
        def hub_card(match):
            code, body = match[1].upper(), match[2]
            if code not in metadata or code in snapshot['retired']:
                return match[0]
            level, category = metadata[code]
            if 'Fundamentals' in snapshot['names'][code] or 'Foundations' in snapshot['names'][code]:
                level = 'Fundamentals'
            body = re.sub(r'<span class="guide-card__hint">.*?</span>',
                          f'<span class="guide-card__hint">{level} · {LABELS[category]}</span>', body)
            return f'<a class="guide-card" data-exam-category="{category}" href="/exams/{code.lower()}/">{body}</a>'
        text = re.sub(r'<a class="guide-card"(?: data-exam-category="[^\"]*")? href="/exams/([a-z]{2}-\d{3})/">(.*?)</a>', hub_card, text, flags=re.S)
        retired = re.search(r'(<section id="fam-retired".*?)(<nav class="guide-grid".*?</nav>)(\s*</section>)', text, re.S)
        if retired:
            text = text[:retired.start()] + retired[1] + '<details class="exam-reference"><summary>Show retired reference pages and next steps</summary>' + retired[2] + '</details>' + retired[3] + text[retired.end():]
    return campaign_links(text, relative)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
    metadata = exam_metadata((ROOT / 'index.html').read_text())
    changed = []
    for path in [path for _, path in published_pages()] + [ROOT / 'exams/_template.html']:
        current = path.read_text(); expected = render(path, current, snapshot, metadata)
        if expected != current:
            changed.append(str(path.relative_to(ROOT)))
            if not args.check: path.write_text(expected)
    if changed and args.check:
        print('Conversion UI is stale:\n' + '\n'.join(changed)); return 1
    print(f'Conversion UI {"OK" if args.check else "synchronised"}: {len(changed)} changed pages'); return 0


if __name__ == '__main__':
    raise SystemExit(main())
