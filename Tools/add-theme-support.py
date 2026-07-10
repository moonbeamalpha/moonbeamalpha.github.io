#!/usr/bin/env python3
"""Add light-theme support (head snippet, stylesheet link, theme.js, nav toggle)
to every exam page + _template.html. Idempotent: pages that already contain the
snippet are skipped. Asserts exactly one match per anchor per file so clone
drift (e.g. the gh-300/gh-900 slim variants) fails loudly instead of silently.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "exams"

SNIPPET = (
    '  <meta name="color-scheme" content="dark">\n'
    '  <script>(function(){try{if(localStorage.getItem(\'am-theme\')===\'light\')'
    '{var d=document;d.documentElement.setAttribute(\'data-theme\',\'light\');'
    'var c=d.querySelector(\'meta[name="color-scheme"]\'),'
    't=d.querySelector(\'meta[name="theme-color"]\');'
    'if(c)c.content=\'light\';if(t)t.content=\'#F5F7FA\';}}catch(e){}})()</script>\n'
)

TOGGLE = (
    '    <button class="theme-toggle" type="button" hidden aria-pressed="false" aria-label="Switch to light theme">\n'
    '      <svg class="theme-toggle__sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>\n'
    '      <svg class="theme-toggle__moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>\n'
    '    </button>\n'
)

EDITS = [
    # (anchor, replacement)
    ('  <meta name="color-scheme" content="dark">\n', SNIPPET),
    ('  </style>\n</head>', '  </style>\n  <link rel="stylesheet" href="/theme-light.css">\n</head>'),
    ('  <script src="/exams/exam.js" defer></script>',
     '  <script src="/exams/exam.js" defer></script>\n  <script src="/theme.js" defer></script>'),
    ('    <a class="site-nav__cta"', TOGGLE + '    <a class="site-nav__cta"'),
]


def process(path: Path) -> str:
    text = path.read_text()
    if 'am-theme' in text:
        return 'skip (already themed)'
    for anchor, replacement in EDITS:
        count = text.count(anchor)
        if count != 1:
            raise AssertionError(f"{path}: anchor {anchor[:48]!r} matched {count} times (want 1)")
    for anchor, replacement in EDITS:
        text = text.replace(anchor, replacement, 1)
    path.write_text(text)
    return 'updated'


def main() -> int:
    targets = sorted(ROOT.glob('*/index.html')) + [ROOT / '_template.html']
    failures = []
    for path in targets:
        try:
            print(f"{path.parent.name + '/' + path.name:42s} {process(path)}")
        except AssertionError as exc:
            failures.append(str(exc))
            print(f"{path.parent.name + '/' + path.name:42s} FAILED")
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
