# Reviewed release-count candidate: 13 October 2026

The daily AZ-400 expansion adds twenty original questions (527 to 547 exam-scoped, 536 to 556 authored). This package stages the generated companion-site synchronization from the exact reviewed app exports without changing published pages, data, practice-preview sources, social images, or the protected count-freeze receipt.

The candidate export has 30 current exams, 12,913 exam-scoped questions, a generated 12,900+ label, and 29 certification paths. It also reconciles earlier unpromoted expansions with current app main. Published production remains at the 12 October freeze: 12,758 exam-scoped questions, 12,700+, 30 exams and 29 paths.

`candidate-exam-counts.json` is copied from the required `sync-marketing-counts.py --refresh --app-repo <isolated-app-checkout>` run. `generated-sync.patch.gz` contains its exact generated HTML/data/social-image changes plus the required llms-full, search-index, asset-version and sitemap regeneration. The generated candidate passed all 23 workflow commands excluding the publication-count freeze; the first CSS attempt encountered sandbox DNS/cache failure, and the isolated-cache network retry passed. The unchanged freeze deliberately rejects promotion before an approved release. The final staging tree must pass the full workflow including the freeze.

The 547-question card was rendered and visually checked; `az-400-preview.jpg` is the reviewed candidate image. The production card is unchanged.

Apply or regenerate this package only after the App Store release is approved and Chris authorizes its counts. Do not update `Tools/production-count-freeze-20261012.json` as part of this review package. At that later point, rebase on current website/app state, regenerate the counts and all dependent assets, and re-run every gate; sitemap dates and any changes since this candidate must be refreshed. The patch is evidence for review, not an automatic deployment instruction. Keep this PR unmerged and unpublished until separately authorized.

App PR: https://github.com/moonbeamalpha/AZ-104-Mastery/pull/896 (head56a7c5212). Both app and staging PRs remain review-only.
