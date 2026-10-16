# Unpublished release count candidate — 16 October 2026

This draft candidate accompanies twenty original AZ-700 additions. The app exports contain 12,983 exam-scoped questions / 12,900+ across 30 current exams and 29 paths. AZ-700 contains 669 exam-scoped questions.

Production remains frozen at 12,758 / 12,700+. This PR changes only this candidate package. Every production HTML, snapshot, preview source, search artifact and social image generated for validation was restored byte-for-byte to the base commit. The production freeze receipt and policy are unchanged.

`exam-counts.json` is generated from the isolated app exports. `generated-site.patch.gz` is the exact deterministic gzip-compressed binary diff of the generated site candidate. `candidate-provenance.json` records its base, paths and before/after hashes. The rendered AZ-700 card was visually checked: the 669-question copy is readable and unclipped.

Candidate checks cover counts/domains, SEO, sitemap, similarity, search, conversion, authored previews, assets, CSS, privacy, performance and whitespace. CSS passed after a network-enabled retry. Final staging checks enforce the production freeze after restoration. The first packaging attempt failed for disk space; the resumed package was regenerated and verified after capacity became available.

Before promotion, wait for App Store approval and explicit owner authorization to update published counts. Regenerate from the approved current app sources, reconcile earlier candidates, rerun all publication checks, and review the resulting diff. No automatic merge or publication.
