# Release-count candidate: 14 October 2026

This package stages the companion synchronization for twenty new PL-300 questions. The app bank grows430→450 authored and418→438 exam-scoped. Candidate exports are12,943 exam-scoped /12,900+,30 exams and29 paths, reconciling other app-main changes since the frozen published snapshot. Production remains12,758 /12,700+.

`candidate-exam-counts.json` is copied from `sync-marketing-counts.py --refresh --app-repo <isolated-app-checkout>`; totals are app-derived. `generated-sync.patch.gz` holds the exact binary diff with generated pages/data/social cards, LLM/search/assets/sitemap. All23 non-freeze workflow commands pass. The reviewed438-question PL-300 card is included as `pl-300-preview.jpg`.

This staging PR changes only this candidate folder. Published pages, production counts, practice previews, social images and the protected freeze receipt remain byte-identical to website main. Final staging checks include the freeze. Nothing is merged or published.

Do not apply the patch before an App Store-approved release and Chris’s explicit count authorization. Regenerate against then-current approved app exports and website state, reconcile older staging PRs, and rerun all gates. The patch is review evidence for this dated source state, not a deployment instruction.

The corresponding app PR and exact CI heads are linked in the PR description after creation. Native content/format and full blueprint evidence live in the app PR.
