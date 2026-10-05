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
SYMBOLS = {'all': 'squares-four', 'infra': 'cloud', 'data-ai': 'database',
           'devops': 'code', 'business': 'brain', 'security': 'lock-key', 'github': 'git-branch'}
FEATURED = ['AZ-900', 'AZ-104', 'AI-901', 'DP-700', 'PL-300', 'SC-900']
ACCESS_TOOL_DISCLOSURES = {
    'AB-650': 'For broader Microsoft 365 and Copilot revision, Pro adds readiness guidance and coaching alongside the question banks.',
    'AI-300': 'Pro unlocks all banks plus the readiness assessment and Answer Coach.',
    'AI-901': 'Start with the fundamentals preview to judge the explanation style. Choose Pro when you want readiness insights and coaching as well as AI practice.',
    'GH-300': 'Pro adds coaching and a readiness forecast while you work towards the GitHub Copilot certification.',
    'GH-900': 'A Foundations bank suits one certification. Pro is the option for guided revision and readiness tools across GitHub and the other supported exams.',
    'PL-300': 'Exam IQ and Answer Coach are Pro benefits, separate from the Power BI bank purchase.',
}
EXAM_HERO_CHROME = ('<a class="conversion-try" href="#question-types">Try a practice question →</a>\n'
                   '<p class="conversion-terms">50+ free questions per exam · No account needed.<br>'
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


def symbol(name, extra_class=''):
    """Decorative, locally hosted Phosphor icons; labels supply the accessible name."""
    return f'<span class="am-symbol {extra_class}" data-symbol="{name}" aria-hidden="true"></span>'


def subject_filters(home=False):
    labels = [('all', 'All'), *LABELS.items()]
    return ('<div class="exam-finder__filters" data-exam-filters hidden role="group" aria-label="Filter exams by subject">' +
            ''.join(f'<button type="button" data-exam-filter="{key}" aria-pressed="{str(key == "all").lower()}">'
                    f'{symbol(SYMBOLS[key])}<span>{html.escape("Azure" if home and key == "infra" else label)}</span></button>'
                    for key, label in labels) + '</div>')


def exam_tier(code, snapshot, metadata):
    if code in snapshot['retired']:
        return 'retired', 'Retired reference', 0
    name = snapshot['names'][code]
    level, category = metadata[code]
    if 'Fundamentals' in name or 'Foundations' in name:
        level = 'Fundamentals'
    return category, level, {'Fundamentals': 1, 'Associate': 2, 'Expert': 3}[level]


def certification_badge(code, stars):
    tier = {2: 'ASSOCIATE', 3: 'EXPERT'}.get(stars)
    return ('<span class="certification-badge" aria-hidden="true">'
            '<img class="certification-badge__shield" src="/exams/images/certification-badge-shield-v3.webp" '
            'alt="" width="300" height="300" loading="lazy" decoding="async">'
            f'<span class="certification-badge__code" data-code="{code}"></span>'
            + (f'<span class="certification-badge__tier" data-tier="{tier}"></span>' if tier else '') +
            f'<span class="certification-badge__stars" data-stars="{stars}">' +
            '<img src="/exams/images/fluent-star-24-filled.svg" alt="" width="24" height="24" loading="lazy">' * stars +
            '</span></span>')


def current_pathways(text, snapshot):
    """Remove retired stations and clean alternatives without inventing new routes."""
    retired = set(snapshot['retired'])
    station_pattern = r'<li class="cert-path__station">.*?</li>'
    or_pattern = r'<span class="cert-path__or">.*?</span>\s*'

    def update_path(match):
        article = match[0]
        stations = re.search(r'(<ol class="cert-path__stations">)(.*?)(</ol>)', article, re.S)
        if not stations:
            return article
        groups = []
        for station in re.findall(station_pattern, stations[2], re.S):
            doc = Document(station).root
            code_node = doc.find(lambda n: 'cert-path__chip-code' in n.attrs.get('class', '').split())
            code = clean(code_node.text()) if code_node else ''
            if not re.search(or_pattern, station, re.S) or not groups:
                groups.append([])
            groups[-1].append((station, code))
        exam_groups = [group for group in groups if any(code in snapshot['exams'] for _, code in group)]
        # A retired destination cannot leave a misleading prerequisite-only path.
        if exam_groups and all(code in retired for _, code in exam_groups[-1]):
            return ''
        output = []
        for group in groups:
            surviving = [(station, code) for station, code in group if code not in retired]
            for index, (station, code) in enumerate(surviving):
                if index == 0:
                    station = re.sub(or_pattern, '', station, flags=re.S)
                if len(group) > len(surviving) == 1:
                    station = station.replace('current prereq option', 'Prerequisite')
                    station = station.replace('current Associate prerequisite', 'Associate prerequisite')
                    station = station.replace('prereq option', 'Prerequisite')
                output.append(station)
        if not output:
            return ''
        return article[:stations.start(2)] + '\n            ' + '\n            '.join(output) + '\n          ' + article[stations.end(2):]

    return re.sub(r'[ \t]*<article class="cert-path">.*?</article>', update_path, text, flags=re.S)


def hub_card(code, snapshot, metadata, reference_hint):
    retired = code in snapshot['retired']
    category, level, stars = exam_tier(code, snapshot, metadata)
    category_attr = '' if retired else f' data-exam-category="{category}"'
    hint = reference_hint if retired else LABELS[category]
    return (f'<a class="guide-card exam-hub-card" data-exam-tone="{category}"{category_attr} href="/exams/{code.lower()}/">'
            + certification_badge(code, stars) +
            f'<span class="exam-hub-card__level">{level}</span>'
            f'<span class="guide-card__kicker">{code}</span>'
            f'<span class="guide-card__name">{html.escape(snapshot["names"][code])}</span>'
            f'<span class="guide-card__hint">{html.escape(hint)}</span>'
            f'<span class="guide-card__more">{"View next steps" if retired else "View exam"}'
            f'{symbol("arrow-right")}</span></a>')


def related_certification_badges(text, snapshot, metadata):
    """Add a shared badge to single-certification related links without rewriting copy."""
    def replace(match):
        attributes, body = match[1], match[2]
        destination = re.search(r'href="/exams/([a-z]{2}-\d{3})/"', attributes)
        label = re.search(r'class="related-card__code">([A-Z]{2}-\d{3})</span>', body)
        code = destination[1].upper() if destination else label[1] if label else None
        if code not in snapshot['exams']:
            return match[0]
        category, _, stars = exam_tier(code, snapshot, metadata)
        body = re.sub(r'<!-- related-certification-badge:start -->.*?<!-- related-certification-badge:end -->',
                      '', body, flags=re.S)
        attributes = re.sub(r' data-certification-card| data-exam-tone="[^"]*"', '', attributes)
        return (f'<a class="related-card" data-certification-card data-exam-tone="{category}"{attributes}>'
                '<!-- related-certification-badge:start -->' + certification_badge(code, stars) +
                '<!-- related-certification-badge:end -->' + body + '</a>')
    return re.sub(r'<a class="related-card"([^>]*)>(.*?)</a>', replace, text, flags=re.S)


def finder_cards(snapshot, metadata):
    current = sorted(set(snapshot['exams']) - set(snapshot['retired']))
    if set(current) - set(metadata):
        raise ValueError('Current exams missing roadmap classification: ' + str(set(current) - set(metadata)))
    def card(code):
        category, level, stars = exam_tier(code, snapshot, metadata)
        name = snapshot['names'][code]
        # The title already conveys the level for names such as Power BI Data Analyst Associate.
        meta = LABELS[category] if level.lower() in name.lower() else f'{level} · {LABELS[category]}'
        return (f'<a class="exam-finder__card exam-mini__tag" data-exam-category="{category}" href="/exams/{code.lower()}/">'
                + certification_badge(code, stars) +
                f'<span class="exam-finder__code">{code}<span aria-hidden="true">↗</span></span>'
                f'<span class="exam-finder__title">{html.escape(name.removeprefix("Microsoft "))}</span>'
                f'<span class="exam-finder__meta">{meta}</span></a>')
    featured = [code for code in FEATURED if code in current]
    # Every current exam stays visible; the subject filters do the narrowing.
    return ('<div class="exam-finder__grid">' + '\n'.join(card(code) for code in featured) + '\n' +
            '\n'.join(card(code) for code in current if code not in featured) + '</div>')


def hero_exam_links(snapshot):
    """Let a visitor jump from the hero to their exam page; retired exams never appear."""
    current = set(snapshot['exams']) - set(snapshot['retired'])
    links = ''.join(f'<li><a href="/exams/{code.lower()}/">{code}<span class="sr-only"> '
                    f'{html.escape(snapshot["names"][code].removeprefix("Microsoft "))}</span></a></li>'
                    for code in FEATURED if code in current)
    return ('<nav class="hero-exams" aria-labelledby="hero-exams-label">'
            '<p class="hero-exams__label" id="hero-exams-label">Which exam are you taking?</p>'
            '<ul class="hero-exams__list">' + links +
            '<li><a class="hero-exams__all" href="#exam-roadmap">All exams <span aria-hidden="true">→</span></a></li>'
            '</ul></nav>')


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
        if placement and not params.get('ct'):
            params['ct'] = stem + '-' + placement
        elif not params.get('ct'):
            params['ct'] = stem + '-body'
        params['pt'] = PROVIDER; params['mt'] = '8'
        if relative != 'exams/_template.html':
            params['ct'] = short_campaign(params['ct'])
        encoded = urlencode(params).replace('%7B', '{').replace('%7D', '}') if relative == 'exams/_template.html' else urlencode(params)
        return tag.replace(found[0], 'href="' + html.escape(url._replace(query=encoded).geturl(), quote=True) + '"')
    text = re.sub(r'<a\b[^>]*>', replace, text)
    def banner(match):
        content = html.unescape(match[1])
        content = re.sub(r',\s*affiliate-data=[^,]*', '', content)
        campaign = stem + '-banner'
        if relative != 'exams/_template.html': campaign = short_campaign(campaign)
        content += ', affiliate-data=pt=' + PROVIDER + '&ct=' + campaign + '&mt=8'
        return '<meta name="apple-itunes-app" content="' + html.escape(content, quote=True) + '">'
    return re.sub(r'<meta name="apple-itunes-app" content="([^\"]*)">', banner, text)


def access_faq(text, code, snapshot):
    """Keep the visible access answer truthful; the FAQ tool owns its JSON-LD."""
    if code not in snapshot['exams']:
        return text
    changed = 0
    def replace(match):
        nonlocal changed
        current = match[0]
        if 'app is free to download' not in current and 'is a retired reference pack' not in current:
            return current
        changed += 1
        paragraph = re.search(r'<div class="faq__answer">\s*<p>(.*?)</p>', current, re.S)
        if not paragraph:
            raise ValueError(f'{code}: access FAQ must contain one answer paragraph')
        if code not in snapshot['retired']:
            # Preserve each exam's authored wording and tool-owned count phrase.
            answer = re.sub(r'a free allowance of ' + re.escape(code) +
                            r' questions(?: so you can try every feature| to try every feature(?: first)?|'
                            r' to try Answer Coach, the readiness gauge, and the adaptive plan before you commit)?',
                            f'50+ free {code} questions and written explanations', paragraph[1])
            disclosure = ACCESS_TOOL_DISCLOSURES.get(code, 'Advanced study tools require Pro.')
            if code == 'PL-300':
                answer = ('The app is free to download. Start with 50+ free PL-300 questions and written explanations '
                          'to see how the revision flow feels. A one-time exam-pack purchase opens the full '
                          f"{snapshot['exams'][code]}-question bank for Power BI practice, or you can choose Pro "
                          'with a subscription or lifetime access.')
            elif code == 'AI-300':
                answer = ('Yes. The app is free to download. Use 50+ free AI-300 questions and written explanations '
                          "as a small preview before paying. To own this exam's content, select the one-time exam-pack purchase "
                          f"for the full bank of {snapshot['exams'][code]} AI-300 practice questions.")
            answer = answer.replace(' Advanced study tools require Pro.', '') if code in ACCESS_TOOL_DISCLOSURES else answer
            if disclosure not in answer:
                answer += ' ' + disclosure
        else:
            answer = (f'{code} is a retired reference pack. Previously purchased access stays available. '
                      'For new study, choose a current exam and start with 50+ free questions and written explanations. '
                      'Pro adds full Exam IQ insights, Answer Coach, the simulator and Ask Aura Preview for supported current exams.')
        return re.sub(r'(<div class="faq__answer">\s*)<p>.*?</p>',
                      lambda paragraph: paragraph[1] + '<p>' + answer + '</p>', current, count=1, flags=re.S)
    result = re.sub(r'<details class="faq">.*?</details>', replace, text, flags=re.S)
    if changed != 1:
        raise ValueError(f'{code}: expected exactly one access FAQ, found {changed}')
    return result


def render(path, text, snapshot, metadata):
    relative = path.relative_to(ROOT).as_posix()
    assets = '<link rel="stylesheet" href="/conversion.css">\n<script src="/conversion.js" defer></script>'
    is_exam = re.fullmatch(r'exams/[a-z]{2}-\d{3}/index.html', relative) or relative == 'exams/_template.html'
    if relative == 'index.html' or is_exam:
        assets += '\n<script src="/practice.js" defer></script>'
    if re.search(r'gtag\([\'"]config[\'"]', text):
        assets += '\n<script src="/app-store-links.js" defer></script>'
    for asset in ['/conversion.css', '/conversion.js', '/practice.js', '/app-store-links.js']:
        versioned = re.search(re.escape(asset) + r'\?v=[0-9a-f]{12}', text)
        if versioned:
            assets = assets.replace('"' + asset + '"', '"' + versioned[0] + '"')
    text = re.sub(r'<script src="/app-store-links\.js(?:\?v=[0-9a-f]{12})?" defer></script>\n?', '', text)
    text = block(text, 'assets', assets, '</head>')
    if relative == 'index.html':
        text = block(text, 'cards', finder_cards(snapshot, metadata), '<!-- exam-roadmap-map:start -->')
        text = block(text, 'hero-exams', hero_exam_links(snapshot), '        <div class="hero-badges">')
        text = re.sub(r'<div class="exam-finder__filters"[^>]*>.*?</div>',
                      lambda _: subject_filters(home=True), text, count=1, flags=re.S)
    if is_exam:
        chrome = EXAM_HERO_CHROME
        code = path.parent.name.upper()
        if code in snapshot['retired']:
            chrome = chrome.replace('50+ free questions per exam', 'Previously purchased pack access')
            chrome = chrome.replace('Full banks: one-time purchase. Pro adds every bank and advanced study tools.',
                                    'For new study, choose a current exam. Pro adds advanced study tools.')
        text = block(text, 'hero', chrome, '          <div class="am-cert-hero__ctas">')
        text = access_faq(text, code, snapshot)
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
        filters = (subject_filters() +
                   '<p class="exam-finder__count" data-exam-count role="status" aria-live="polite"></p>')
        filters = '<div class="container exam-finder__controls">' + filters + '</div>'
        text = block(text, 'hub-filters', filters, '<section id="fam-azure"')
        def replace_hub_card(match):
            code, body = match[1].upper(), match[2]
            hint = re.search(r'<span class="guide-card__hint">(.*?)</span>', body, re.S)
            return hub_card(code, snapshot, metadata, html.unescape(hint[1]) if hint else '')
        text = re.sub(r'<a class="guide-card(?: exam-hub-card)?"[^>]* href="/exams/([a-z]{2}-\d{3})/">(.*?)</a>',
                      replace_hub_card, text, flags=re.S)
        text = re.sub(r'<section id="(fam-(?:azure|ai|data|security|github))" class="container"(?: data-exam-section)?>',
                      r'<section id="\1" class="container" data-exam-section>', text)
    text = related_certification_badges(text, snapshot, metadata)
    text = current_pathways(text, snapshot)
    def pathway_tier(match):
        opening, level, body = match[1], match[2], match[3]
        body = re.sub(r'<span class="cert-path__chip-tier"[^>]*></span>', '', body)
        return (opening + f'<span class="cert-path__chip-tier" data-tier="{level.upper()}" aria-hidden="true"></span>'
                + body + match[4])
    text = re.sub(r'(<(?:a|span)\b[^>]*class="cert-path__chip[^\"]*"[^>]*data-cert-level="(associate|expert)"[^>]*>)(.*?<span class="cert-path__chip-role">.*?</span>\s*)(</(?:a|span)>)',
                  pathway_tier, text, flags=re.S)
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
