#!/usr/bin/env python3
"""Join local aggregate GA4 clicks and Apple first-time downloads by campaign token."""
import argparse
import csv
from collections import Counter
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs


def aggregate(click_rows, download_rows):
    clicks, downloads = Counter(), Counter()
    for row in click_rows:
        url = urlsplit(row['link_url']); query = parse_qs(url.query)
        if url.hostname != 'apps.apple.com' or url.path != '/app/id6760594569' or query.get('pt') != ['128558698']:
            continue
        campaign = query.get('ct', [''])[0]
        if not re.fullmatch(r'[a-z0-9-]{1,30}', campaign): raise ValueError('Unexpected site campaign token')
        count = int(row['clicks'])
        if count < 0: raise ValueError('Click totals cannot be negative')
        clicks[campaign] += count
    for row in download_rows:
        campaign = row['campaign']
        if not re.fullmatch(r'[a-z0-9-]{1,30}', campaign): raise ValueError('Unexpected site campaign token')
        # An empty/suppressed Apple metric remains unknown, never a manufactured zero.
        if row['first_time_downloads'] == '': continue
        count = int(row['first_time_downloads'])
        if count < 0: raise ValueError('Download totals cannot be negative')
        downloads[campaign] += count
    return [{'campaign': campaign, 'outbound_clicks': clicks.get(campaign, ''),
             'first_time_downloads': downloads.get(campaign, ''),
             'downloads_per_click': round(downloads[campaign] / clicks[campaign], 4) if clicks[campaign] and campaign in downloads else ''}
            for campaign in sorted(clicks.keys() | downloads.keys())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clicks', type=Path, required=True); parser.add_argument('--downloads', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    with args.clicks.open(newline='') as click_file, args.downloads.open(newline='') as download_file:
        rows = aggregate(csv.DictReader(click_file), csv.DictReader(download_file))
    with args.output.open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['campaign', 'outbound_clicks', 'first_time_downloads', 'downloads_per_click'])
        writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows)} campaign aggregates to {args.output}. Unreported values remain blank.')


if __name__ == '__main__': main()
