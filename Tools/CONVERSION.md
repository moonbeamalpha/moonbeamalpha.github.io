# Marketing conversion UI

The homepage follows a shorter decision path: understand the app through three real study screens, find an exam,
try three authored questions, compare access options, then download.
The roadmap is an optional desktop view. Catalogue-derived cards supply exam
titles, levels and subject areas; retirement references remain in disclosures.

The Ask Aura feature links to `/ask-aura/`, with a character hero, reviewed
capability examples, a real in-app session and the existing video. The YouTube
iframe loads only on play; its external link also works without JavaScript.
The page states the Pro preview and generative-explanation limits beside the
hero download action. The search index uses this page instead of `/#ask-aura`.

The practice preview keeps answer choices compact after grading. It presents
the correct rationale first and keeps every other authored rationale in a
native disclosure. Lettered choices are grouped under the complete prompt;
announced feedback, explicit answer labels and reset support keyboard use.

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

`sync-home-practice.py --app-repo <path>` owns the six homepage samples and
`data/home-practice.json`; every option rationale and the complete prompt are
retained, with a no-JavaScript answer disclosure. Switching exams preserves
local progress; Restart clears only that exam.

`optimise-marketing-seo.py --app-repo <path>` refreshes the practice samples from
the app's authored banks. Selection requires an independent scenario and written
reasoning for every option. It retains full context/stems and writes the small,
already-public sample snapshot in `data/practice-previews.json`. The snapshot
lets CI catch a missing condition or rationale without an app checkout. Sample
answers stay in memory. No answer or search-query events are sent or saved.

Pricing copy follows `EntitlementManager.swift`, `ExamStoreView.swift`,
`PaywallView.swift` and reviewed Aura product help: free starter sets, one-time
individual banks, and monthly/annual/lifetime Pro. UK reference prices, verified in App Store Connect on 1 October 2026, are
£4.99 once for AZ-900/AZ-104 packs, £9.99 monthly Pro and £49.99 annual Pro.
They are dated and qualified beside the cards; the app confirms the local price.
Recheck these four products in App Store Connect before changing this copy.
No lifetime price or universal pack price is inferred. The 50+ free allowance
is checked against every marketing-eligible catalogue entry by `sync-home-practice.py`. Pro includes the full Exam IQ tools, Answer Coach, the simulator
and Ask Aura preview; the preview does not enable generative explanations.

## Measurement

The delegated `app-store-links.js` event supplies `app_store_click` with only a
validated static `store_campaign` and beacon transport. It ignores local preview
hosts, other domains/apps and malformed campaign strings. It never reads answers,
search text, page query strings or identifiers. Existing GA4 enhanced outbound
`click` events are a separate metric; do not sum them with `app_store_click`.
Register `store_campaign` as an event-scoped GA4 custom dimension to compare
placements. Analytics availability/consent still controls whether an event is sent. Static links and QR codes contain the existing
provider token `128558698`, media type `8` and distinct placement campaigns. Native
Safari's Smart App Banner preserves the exam deep link and includes attribution.
All campaign tokens stay within Apple's current 30-character limit.

Use the same date range/time zone for both local aggregate exports:

1. Export GA4 `app_store_click` counts by `store_campaign`, excluding internal
   traffic. Normalize columns to `store_campaign,clicks`. The report also accepts
   the older `link_url,clicks` enhanced-measurement export. Use one metric per
   comparison; do not export users, query text or identifiers.
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

## Validation on 1 October 2026

The updated homepage was visually reviewed at 1280px desktop width, and at
320px, 390px and 430px phone widths in both actual themes with reduced motion.
The six-question flow passed correct/wrong feedback, retry, next, exam-switch
position preservation, completion, selected-exam restart and campaign matching.
No-JavaScript checks confirmed six complete question/answer disclosures.
The comparison table scrolls within its region without widening the page.
Existing images were reused; the connected step markers and small welcoming Aura
add visual guidance using existing small assets. Learner proof was excluded.

The App Store source update is a companion change in AZ-104-Mastery: descriptions
and draft hero figures derive from its export. Both 2.1 English descriptions and
both 2.0/2.1 promotional texts were updated and read back through App Store Connect.
The draft's two hero images processed successfully; its other screenshots and
Watch set were preserved. Published screenshots require the next approved release.
