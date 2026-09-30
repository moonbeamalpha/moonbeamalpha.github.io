# Marketing conversion UI

The homepage follows a shorter decision path: understand the app, find an exam,
try an authored question, compare access options, then explore tools and download.
The roadmap is an optional desktop view. Catalogue-derived cards supply exam
titles, levels and subject areas; retirement references remain in disclosures.

`sync-conversion-ui.py` maintains shared assets, the exact exam purchase/methodology
component, placement links, Smart App Banner attribution and exam cards. It covers
published sitemap pages and the exam template. Its `--check` mode is read-only.
The similarity baseline and tolerance are unchanged. Only the byte-exact shared
purchase/navigation component is excluded from editorial similarity; modified
prose stays in the comparison.

Run after catalogue or UI changes:

```sh
python3 Tools/sync-conversion-ui.py
python3 Tools/build-download-qr.py       # requires segno==1.6.6
python3 Tools/build-search-index.py
python3 Tools/version-static-assets.py
python3 Tools/update-sitemap-lastmod.py
python3 Tools/check-conversion-ui.py
```

`optimise-marketing-seo.py --app-repo <path>` refreshes the practice samples from
the app's authored banks. Selection requires an independent scenario and written
reasoning for every option. It retains full context/stems and writes the small,
already-public sample snapshot in `data/practice-previews.json`. The snapshot
lets CI catch a missing condition or rationale without an app checkout. Sample
answers stay in memory. No answer or search-query events are sent or saved.

Pricing copy follows `EntitlementManager.swift`, `ExamStoreView.swift`,
`PaywallView.swift` and reviewed Aura product help: free starter sets, one-time
individual banks, and monthly/annual/lifetime Pro. Region-dependent prices are
shown in the app. Pro includes the full Exam IQ tools, Answer Coach, the simulator
and Ask Aura preview; the preview does not enable generative explanations.

## Measurement

Existing GA4 enhanced measurement supplies outbound `click` events and `link_url`.
No second click logger is installed. Static links and QR codes contain the existing
provider token `128558698`, media type `8` and distinct placement campaigns. Native
Safari's Smart App Banner preserves the exam deep link and includes attribution.
All campaign tokens stay within Apple's current 30-character limit.

Use the same date range/time zone for both local aggregate exports:

1. Export GA4 outbound `click` counts by `link_url` for `apps.apple.com`, excluding
   internal traffic. Normalize columns to `link_url,clicks`. Do not export users,
   query text or identifiers.
2. Export Apple App Analytics First-Time Downloads by Campaign (or use the detailed
   App Downloads report and aggregate first-time downloads locally). Normalize
   columns to `campaign,first_time_downloads`. Keep unavailable/withheld values blank.
3. Join the aggregates locally:

```sh
python3 Tools/report-download-funnel.py --clicks /private/tmp/ga4-clicks.csv \
  --downloads /private/tmp/apple-downloads.csv --output /private/tmp/download-funnel.csv
```

Compare the hero, pricing, preview, sticky and QR placements, then compare periods
before/after release. `downloads_per_click` is a descriptive aggregate ratio: repeat
clicks, attribution windows, storefront behavior and reporting thresholds mean it
is not a person-level conversion probability. A QR scan has no browser click and
can legitimately have only an Apple metric. Do not replace missing Apple rows with
zero or claim a measured uplift before these reports contain data.

Apple attributes first-time downloads within 24 hours of a campaign link and
applies minimum reporting thresholds/privacy suppression. See [Apple campaign
links](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links).
Native Smart App Banner and QR handoff should also be checked on a physical iPhone
in Safari before publishing; a desktop web listing failure alone does not establish
whether an app is available in a user's storefront.
