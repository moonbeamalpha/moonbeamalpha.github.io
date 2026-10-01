#!/usr/bin/env python3
"""Materialise shared search controls on published pages and the exam template."""
from __future__ import annotations

import argparse
import re
import sys
from search_common import ROOT, published_pages

ICON = '<svg class="am-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>'
TRIGGER = ('<button class="am-search-trigger" type="button" data-search-open hidden '
           'aria-label="Search exams, guides and topics" aria-haspopup="dialog" aria-controls="am-search-dialog">'
           + ICON + '<span>Search</span><kbd aria-hidden="true">⌘ K</kbd></button>')


def widget(prefix, inline=False):
    filters = ''.join(f'<button type="button" data-search-kind="{value}" aria-pressed="{str(value == "all").lower()}">{label}</button>'
                      for value, label in [('all', 'All'), ('exam', 'Exams'), ('guide', 'Guides'), ('page', 'Pages')])
    examples = ''.join(f'<button type="button" data-search-example="{value}">{value}</button>'
                       for value in ['AZ-104', 'Security', 'Copilot', 'Fabric'])
    return f'''<div class="am-search{' am-search--inline' if inline else ''}" data-am-search hidden>
      <div class="am-search-top">
        <label class="am-search-label" for="{prefix}-query">Find an exam, guide or topic</label>
        <form class="am-search-form" role="search" aria-label="{'Browse' if inline else 'Site'} search">
          {ICON}
          <input class="am-search-input" id="{prefix}-query" type="search" maxlength="120" placeholder="Search exams, guides and topics…" autocomplete="off" spellcheck="false" aria-controls="{prefix}-results">
          <button class="am-search-clear" type="button" data-search-clear hidden aria-label="Clear search">×</button>
        </form>
        <div class="am-search-filters" role="group" aria-label="Result type">{filters}</div>
        <p class="am-search-status" data-search-status role="status" aria-live="polite" aria-atomic="true">Find your next exam, guide or topic.</p>
      </div>
      <div class="am-search-scroll">
        <div class="am-search-examples" data-search-examples role="group" aria-label="Try a search">{examples}</div>
        <ul class="am-search-results" id="{prefix}-results" data-search-results aria-label="Search results"></ul>
        <details class="am-search-related" data-search-related hidden><summary>Related results</summary><ul class="am-search-results" data-search-related-results aria-label="Related search results"></ul></details>
        <button class="am-search-action" type="button" data-search-more hidden>Show more</button>
        <button class="am-search-action" type="button" data-search-retry hidden>Try again</button>
        <div class="am-search-browse"><a href="/exams/">Browse exams →</a><a href="/guides/">Study guides →</a></div>
      </div>
    </div>'''


def block(name, content):
    return f'<!-- search-{name}:start -->\n{content}\n<!-- search-{name}:end -->'


def replace_block(text, name, content, anchor, before=True):
    expected = block(name, content)
    pattern = rf'<!-- search-{name}:start -->.*?<!-- search-{name}:end -->'
    matches = re.findall(pattern, text, re.S)
    if len(matches) > 1:
        raise ValueError(f'Duplicate search {name} block')
    if matches:
        return re.sub(pattern, lambda _: expected, text, count=1, flags=re.S)
    if text.count(anchor) != 1:
        raise ValueError(f'Search anchor {anchor[:60]!r} must occur exactly once')
    return text.replace(anchor, expected + '\n' + anchor if before else anchor + '\n' + expected, 1)


def render_page(path, text):
    relative = path.relative_to(ROOT).as_posix()
    if relative == 'index.html':
        text = replace_block(text, 'trigger', '<li class="am-search-nav-item">' + TRIGGER + '</li>', '<li><button class="theme-toggle"')
    elif re.search(r'<header class="site-nav"', text):
        anchor = ('    <button class="theme-toggle"' if '    <button class="theme-toggle"' in text
                  else '    <a class="site-nav__cta"')
        text = replace_block(text, 'trigger', TRIGGER, anchor)
    else:
        text = replace_block(text, 'trigger', '<header class="am-search-legacy-nav"><a href="/">Azure Mastery</a>' + TRIGGER + '</header>', '<div class="container">')
    # Give icon-only mobile branding an accessible name independent of hidden text.
    text = re.sub(r'(<a\b(?=[^>]*class="(?:nav-brand|site-nav__brand)")(?=[^>]*href=)[^>]*)(>)',
                  lambda m: m[0] if 'aria-label=' in m[1] else m[1] + ' aria-label="Azure Mastery home"' + m[2], text)
    assets = ('<link rel="stylesheet" href="/search.css">\n'
              '<script src="/search.js" data-search-index="/data/search-index.json" defer></script>')
    # Keep existing content-hash versions when checking/re-syncing component markup.
    current_assets = re.search(r'<!-- search-assets:start -->(.*?)<!-- search-assets:end -->', text, re.S)
    if current_assets:
        for plain in ['/search.css', '/search.js', '/data/search-index.json']:
            versioned = re.search(re.escape(plain) + r'\?v=[0-9a-f]{12}', current_assets[1])
            if versioned:
                assets = assets.replace('"' + plain + '"', '"' + versioned[0] + '"')
    text = replace_block(text, 'assets', assets, '</head>')
    dialog = ('<dialog class="am-search-dialog" id="am-search-dialog" aria-labelledby="am-search-title">\n'
              '  <div class="am-search-dialog__header"><h2 id="am-search-title">Search Azure Mastery</h2>'
              '<button class="am-search-close" type="button" data-search-close aria-label="Close search">×</button></div>\n'
              + widget('am-site-search') + '\n</dialog>')
    text = replace_block(text, 'dialog', dialog, '</body>')
    if relative in {'index.html', 'exams/index.html'}:
        if relative == 'index.html':
            # The shared search sits immediately above the ordinary exam finder.
            match = re.search(r'<[^>]+class="exam-finder__filters"[^>]*>', text)
            if not match:
                raise ValueError('Missing exam finder filters')
            anchor = match[0]
        else:
            anchor = '    <section id="fam-azure"'
            match = re.search(r'<section\b[^>]*id="fam-azure"[^>]*>', text)
            if not match:
                raise ValueError('Missing exam hub family')
            anchor = match[0]
        inline = widget('am-browse-search', True)
        if relative == 'exams/index.html':
            inline = '<div class="container am-search-hub">\n' + inline + '\n</div>'
        text = replace_block(text, 'inline', inline, anchor)
    target = re.search(r'<main\b[^>]*>', text) or re.search(r'<h1\b[^>]*>', text)
    if not target:
        raise ValueError('Missing skip-navigation destination')
    opening = target[0]
    identifier = re.search(r'\bid="([^"]+)"', opening)
    target_id = identifier[1] if identifier else 'main-content'
    if not identifier:
        opening = opening[:-1] + f' id="{target_id}">'
    if 'tabindex=' not in opening:
        opening = opening[:-1] + ' tabindex="-1">'
    text = text[:target.start()] + opening + text[target.end():]
    body = re.search(r'<body\b[^>]*>', text)[0]
    return replace_block(text, 'skip', f'<a class="am-skip-link" href="#{target_id}">Skip to content</a>', body, before=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    paths = [path for _, path in published_pages()] + [ROOT / 'exams/_template.html']
    changed = []
    for path in paths:
        current = path.read_text()
        expected = render_page(path, current)
        if current != expected:
            changed.append(str(path.relative_to(ROOT)))
            if not args.check:
                path.write_text(expected)
    if changed and args.check:
        print('Search UI is stale:\n' + '\n'.join(changed), file=sys.stderr)
        return 1
    print(f'Search UI {"OK" if args.check else "synchronised"}: {len(paths)} pages')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
