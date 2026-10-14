# Release-count candidate: 14 October 2026

This package stages the companion synchronization for twenty new PL-300 questions. The app bank grows430→450 authored and418→438 exam-scoped. Candidate exports are12,943 exam-scoped /12,900+,30 exams and29 paths, reconciling other app-main changes since the frozen published snapshot. Production remains12,758 /12,700+.

`candidate-exam-counts.json` is copied from `sync-marketing-counts.py --refresh --app-repo <isolated-app-checkout>`; totals are app-derived. `generated-sync.patch.gz` holds the exact binary diff with generated pages/data/social cards, LLM/search/assets/sitemap. All23 non-freeze workflow commands pass. The reviewed438-question PL-300 card is included as `pl-300-preview.jpg`.

This staging PR changes only this candidate folder. Published pages, production counts, practice previews, social images and the protected freeze receipt remain byte-identical to website main. Final staging checks include the freeze. Nothing is merged or published.

Do not apply the patch before an App Store-approved release and Chris’s explicit count authorization. Regenerate against then-current approved app exports and website state, reconcile older staging PRs, and rerun all gates. The patch is review evidence for this dated source state, not a deployment instruction.

The corresponding app PR and exact CI heads are linked in the PR description after creation. Native content/format and full blueprint evidence live in the app PR.

## PR901 review refresh

Owner-requested review retained all20 additions, repaired five existing app records, and remapped the key-column item to model properties. The app PL300 content version is1.58, and candidate domain counts now read prepare117/model114/visualize127/manage80. Candidate totals and per-exam438 count are unchanged from initial staging; rendered social assets are retained byte-for-byte. The candidate was applied locally, refreshed from the final reviewed app exports, and passed23 non-freeze gates; production files were then restored before the24 staging gates. Website PR67 stays draft, unmerged and unpublished.
