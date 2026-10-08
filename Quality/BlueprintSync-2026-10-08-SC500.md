# SC-500 count synchronization — 8 October 2026

This branch is based on pending site PR #58 at 41fd54727ba019b74afe3c560ee830379dd93682. Its dependency chain is #57 → #58 → this PR. It is not published or merged.

App exports supply 30 current exams, 12,818 exam-scoped questions (12,800+), and 472 SC-500 questions. SC-500 domain counts are 118 identity, 123 data/network, 118 compute, 113 posture. No count is hand-authored.

Ran sync-marketing-counts.py --refresh against the isolated app checkout, refreshed SC-500 and its AZ-500 related card, generated search/LLM data, versioned search-index references, aligned the two material page dates, and regenerated sitemap dates from complete Git history. Other HTML changes are shared search-index cache references; existing editorial previews remain intact. Rendered and visually inspected the SC-500 472 card, 12,800+ OpenGraph card and LinkedIn banner.

All 22 actual site workflow checks pass, including snapshot/count/domain sync, unchanged similarity ratchet, sitemap/SEO, UI/search/asset/QR/CTA/FAQ/GA/footer/help contracts, CSS and performance checks. No baseline was changed. Local refresh does not publish the site. Review the app PR and the site stack before any later publication decision.
