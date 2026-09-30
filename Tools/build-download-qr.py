#!/usr/bin/env python3
"""Build deterministic, attributed App Store QR assets (pip install segno==1.6.6)."""
import argparse
import io
import json
from pathlib import Path
from urllib.parse import urlencode
import segno

ROOT = Path(__file__).resolve().parents[1]


def qr_assets():
    snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
    for code in ['app-store', 'ask-aura', *sorted(code.lower() for code in snapshot['exams'])]:
        campaign = {'app-store': 'site-home-qr', 'ask-aura': 'ask-aura-qr'}.get(code, 'exam-' + code + '-qr')
        url = 'https://apps.apple.com/app/id6760594569?' + urlencode({'ct': campaign, 'pt': '128558698', 'mt': '8'})
        qr = segno.make(url, error='m', micro=False)
        buffer = io.BytesIO(); qr.save(buffer, kind='svg', scale=4, border=4, dark='#0b1220', light='#fff')
        svg = buffer.getvalue().decode().replace('<svg ', '<svg data-download-url="' + url.replace('&', '&amp;') + '" ', 1)
        yield ROOT / 'images/qr' / (code + '.svg'), svg, qr, url


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    stale = []
    for path, expected, _, _ in qr_assets():
        if not path.exists() or path.read_text() != expected:
            stale.append(path.name)
            if not args.check: path.write_text(expected)
    if stale and args.check:
        print('Stale download QR assets: ' + ', '.join(stale)); return 1
    print('Download QR assets OK' if args.check else 'Download QR assets generated'); return 0


if __name__ == '__main__':
    raise SystemExit(main())
