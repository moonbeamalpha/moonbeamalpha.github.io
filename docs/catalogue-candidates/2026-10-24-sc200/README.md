# SC-200 catalogue candidate — 24 October 2026

This is an **inert, unpublished candidate** for [app PR #956](https://github.com/moonbeamalpha/AZ-104-Mastery/pull/956), branch `codex/blueprint-coverage-20261024`. It records the generated effect of twenty net-new SC-200 questions: 393 exam-scoped SC-200 questions, domain counts 170/139/84, and 13,103 exam-scoped questions across 30 current exams (generated label 13,100+).

`Tools/sync-marketing-counts.py --refresh --no-render --app-repo <isolated-app-worktree>` generated `exam-counts.json`; `catalog-totals.json` is copied verbatim from the app export. The manifest binds the three app input files and records which temporary public files were restored.

The site's approved v2.1.0 build 50 baseline remains 13,003 questions / 13,000+. Every existing public file, practice preview, social asset and production-freeze receipt remains byte-identical to the site branch base. No browser code or deployment workflow reads this candidate directory.

Before promotion, regenerate against the exact next App Store approved release and obtain the owner's explicit count-publication authorization, then run the normal site refresh, rendering and validation workflow. Do not copy this open-content snapshot directly into production. This PR is intentionally draft and must remain unpublished.

This snapshot includes all prior unpublished app-main additions as well as today’s twenty; its 13,103 total is not a claim that the approved public 13,003 baseline increased by only twenty. App head `c9d415a6ef9f1dba486c01d53f0bed8a86351502` passed the full 56-command local content job, 68 pinned simulator tests and 204/204 SC-200 resource URLs. Exact-head GitHub validation is recorded in the linked app PR.
