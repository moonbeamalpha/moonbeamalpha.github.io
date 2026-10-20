# Marketing release 2.1.0 review

App Store Connect checked 20 October 2026: version 2.1.0, READY_FOR_SALE,
build 50, build ID 050e1477-63b7-4361-9997-33458635556a. Local signed archive:
18 October 2026, 23:57. All 35 banks and the catalogue match app commit
f873162b6f28d161ad4a90a0cd7466ce8b48c55a byte-for-byte (36/36 checks).

Counts are regenerated from that source: 13,003 exam-scoped questions,
30 current exams, 29 current certification paths. This incorporates the
released additions behind site PRs #68 (AZ-900), #69 (AZ-700), #71 (AI-200).
Site PRs #72–75 remain unpublished because their app changes are not in build 50.
Their candidate packages are preserved. App PRs #923, #930, #938 and #946
were still open when checked; their counts are not published here.

Feature copy follows merged app PRs #920/#926 (Duo), #922/#924/#928
(motion and Exam IQ milestones), #927 (scenario sections), #931/#932/#937
(answer review and adaptive controls), #921/#925/#933/#936 (bounded Preview
copy, feedback and layout). Watch PRs #940–944 merged after build 50 upload;
this update does not advertise that redesign as a 2.1.0 feature.
The existing committed Duo section (8044193) was ported with current generated
outputs rather than applying its obsolete count/cache-hash changes.

AI-200 editorial promotion review: official study guide checked live on
20 October 2026, https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200 .
The heading is effective 7 October 2026. Skills-at-a-glance says data management
30–35%; the detailed heading still says 25–30%. The change log confirms an
increase. All three site surfaces now state the October date and summary
weight, explicitly disclose the source discrepancy, and retain the other
three domain weights. No app content or review fingerprint was changed.

Screenshots: see marketing-v210-captures.json. Authentic 2.1.0 simulator PNGs
were proportionally downscaled and encoded as WebP. Versioned image names
avoid serving old screenshots from the image cache. New iPad frames preserve
3:4 captures; source screenshots are not stretched. Ask Aura screenshot copy
now describes the captured RBAC explanation rather than the older 15-minute
plan. Existing Mac captures remain the latest available and were retained.

Device illustrations were generated with the built-in imagegen tool, then
encoded as WebP. They are labelled illustrations and are not physical-device
acceptance evidence. Exact image-generation direction:
- Dark: one graphite titanium book-style iPhone Duo, semi folded about 125
  degrees, three-quarter studio view, authentic dark Today capture across the
  continuous inner display, deep navy background, restrained blue glow, no
  extra phones/logos/text, landscape 1536×1024.
- Light: edit that exact render; preserve pose, geometry, framing and shell;
  replace screen with authentic light Today capture; ice-white/light-blue
  studio background and soft shadow; same 1536×1024 output.

Final assets: images/iphone-duo-semi-folded-v210.webp and
images/iphone-duo-semi-folded-v210-light.webp. The existing theme toggle swaps
both the mockups and all refreshed screenshot pairs.
