# DP-300 coverage candidate — 28 October 2026

**Inert draft candidate; no public count update.** Linked app [PR #982](https://github.com/moonbeamalpha/AZ-104-Mastery/pull/982), exact head `bbde82ba2154eb191872d5450d5c979a5544cbb6`, adds twenty DP-300 questions. The generated candidate has 13,183 exam-scoped questions, the 13,100+ label, and 448 DP-300 exam-scoped questions. The source manifest binds every consumed app export and scorecard.

`catalog-totals.json` is copied verbatim from the app generator. `exam-counts.json` was produced by `Tools/sync-marketing-counts.py --refresh --no-render` against the exact reviewed app worktree. All 366 pre-existing tracked site files were then restored and verified byte-identical to main; this PR changes only four documents in this candidate directory. No production snapshot, page, social image, sitemap, search asset or approved-release freeze receipt changes.

The public site retains the approved v2.1.0 build-50 baseline: 13,003 / 13,000+, 30 current exams and 29 paths. These candidate files are not consumed by public renderers. All 21 local site workflow blocks passed; the pinned CSS command needed a network retry after sandbox DNS failure. Exact-head PR CI will be checked after creation.

Before promotion, wait for the next approved app release and explicit owner publication authorization, regenerate from that exact release, and rerun all applicable public sync/render and release-freeze checks. App merge alone is not publication authorization. Earlier candidate PRs, including #83, remain separate historical proposals; this draft does not require or publish them.
