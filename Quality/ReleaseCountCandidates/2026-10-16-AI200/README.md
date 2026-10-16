# Unpublished AI-200 release candidate — 16 October 2026

This candidate accompanies [app PR #919](https://github.com/moonbeamalpha/AZ-104-Mastery/pull/919) at `5843715cac83fe92040bcc9188933d1b4c1930f9`: twenty original AI-200 questions, increasing its
exam-scoped count from 280 to 300. App exports contain 13,003 exam-scoped
questions / 13,000+ across 30 current exams and 29 paths. The app uses the
October 7 guide and 30–35% data allocation, preserving merged PR #918.

Production remains on the approved v2.0.2 build49 snapshot: 12,943 / 12,900+.
Every generated production file was restored byte-for-byte to base commit
`9cb686a`. This draft changes only this candidate package; its baseline receipt,
production HTML, catalogue, previews, search assets and social images are unchanged.

`exam-counts.json` is generated from the isolated app exports.
`generated-site.patch.gz` is the exact deterministic gzip-compressed binary diff
of the generated catalogue candidate. `candidate-provenance.json` records its
base, generated paths and before/after hashes. The AI-200 card was visually
checked: the 300-question label is readable and unclipped. Refreshing against
the integrated app sources produced the identical snapshot.

All 24 candidate checks passed. All 25 staging checks passed after restoration,
including the approved production count freeze. They cover counts and domains,
SEO, sitemap, similarity, search, conversion, previews, assets, CSS, privacy,
performance and whitespace.

This package synchronizes catalogue counts. Existing public AI-200 editorial
pages still describe the May outline; they require source review against the
October guide before any future promotion. Count checks do not certify that copy.

Before promotion, obtain approval for a later App Store release and explicit
owner authorization to update published counts. Regenerate from that approved
source, reconcile older candidates, review public guide copy, and rerun all
publication checks. No automatic merge or publication.
