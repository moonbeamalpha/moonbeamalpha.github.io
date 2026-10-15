# AZ-900 release count synchronization candidate

Validated future-release candidate for [app blueprint expansion PR914](https://github.com/moonbeamalpha/AZ-104-Mastery/pull/914). Candidate snapshot:12,963 exam-scoped questions/12,900+,30current exams/29paths; AZ-900424. Production remains12,758/12,700+.

`candidate.patch.gz` preserves the complete generated HTML/data/preview/search/social-image/sitemap change; `exam-counts.json` is the exact tool-derived candidate export. `manifest.json` binds candidate and production bytes. The424-question AZ-900 card was rendered and visually inspected. All24 nonfreeze workflow checks passed, including a successful CSS network/cache retry.

This folder does not promote counts. Before promotion, obtain AppStore-approved release and explicit owner count authorization, regenerate against the approved app and current site, reconcile older candidates (including PR67), and rerun all current gates. Do not apply this historical patch blindly after later source changes.

Frozen staging tree: all25 current workflow/whitespace checks passed, including the production-count-freeze gate. Every one of the87 run-owned production paths matches the baseline byte-for-byte. Initial restore failed only because its Git index is outside the app sandbox; the scoped permission retry restored all paths successfully.

The exact patch is gzip-compressed to retain its context whitespace as data. Decompress before inspection; uncompressed SHA256 is in the manifest. Staged whitespace validation passes.
