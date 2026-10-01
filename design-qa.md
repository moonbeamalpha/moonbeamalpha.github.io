# Exam library visual QA — 1 October 2026

**Final result: passed**

No actionable P0/P1/P2 findings remain. This is a reference-led refinement of
Azure Mastery's existing design, rather than a pixel clone of Learn Azure.

## Source and rendered evidence

Source visual truth:

- Learn Azure exam-card reference: `/var/folders/dz/dyy7dm995kz71qsjqhv24mq80000gn/T/codex-clipboard-9c8f7d94-8c9e-4191-be50-b82f1a3e65b1.png` — 2804×1526.
- Existing pathway shield: `exams/images/certification-badge-shield.webp` — 300×300 transparent artwork.
- Expert star reference: `/tmp/codex-remote-attachments/01a0f69c-0d3c-77c0-a7a8-6c5308854827/3B2D4337-8EF6-4B78-8285-3CB41C3A9037/1-Photo-1.jpg`.
- Ribbon correction reference: `/tmp/codex-remote-attachments/01a0f69c-0d3c-77c0-a7a8-6c5308854827/A5BF7702-85F0-4B6F-8C63-363DDC867C90/1-Pasted-Image-1.jpg` — 1280×673.

Implementation URLs: `http://127.0.0.1:8751/exams/?am_internal=1` and
`http://127.0.0.1:8751/exams/az-104/?am_internal=1#cert-paths`.

All implementation images below are in
`/Users/chris/.codex/visualizations/2026/10/01/01a0f69c-0d3c-77c0-a7a8-6c5308854827/`.

Full-view comparisons used `exam-library-light-1280.png`,
`azure-exam-cards-light.png` and `azure-exam-cards-dark.png` alongside the source
card reference. They preserve the reference's shield/code/title/action hierarchy
while retaining Azure Mastery's fonts, theme and subject colours.

Focused comparisons used `expert-shield-light-1280.png` (112×113 capture for a
112×112 CSS badge) and `pathway-expert-light-1280.png` (113×126 capture), together with the star and ribbon
references. These confirm clean asset edges, a centred code and the lowered
centre star. `certification-pathways-dark-390.png` verifies the smaller layout.

Captures use CSS pixels (`scale: css`), independent of browser device density.
Desktop viewport: 1280×1000; mobile: 390×1000. General responsive checks also
cover 320, 768 and 1440px widths. Source photos are differently sized crops and
serve as shape/alignment references; they are not interpreted as equal-size
whole-page pixel targets.

## Required fidelity surfaces

- **Fonts and typography:** existing Outfit display/code text and DM Sans body
  text remain coherent with the site. Complete exam names wrap naturally;
  labels and actions stay readable without truncation. The shield's embedded
  `CERTIFICATION` is crisp at both rendered sizes.
- **Spacing and layout:** four desktop columns, three intermediate columns,
  two small-tablet columns and one phone column. Card actions align; the shield,
  level, code and title have distinct spacing. Hidden families remove their
  headings and whitespace. No viewport overflow at tested widths.
- **Colours and tokens:** existing subject tokens retained, with readable
  light Security and dark Azure label colours. Lowest measured level-label
  contrast is 4.57:1 light / 4.55:1 dark. Original pathway emphasis remains.
- **Image quality:** shared transparent 300px WebP, no corner halos, crisp navy
  border and balanced white ribbon. Fluent stars remain separate. Expert stars
  follow the point; centre star drops 5px in cards and 6px in pathways. Code
  stays centred on both shield sizes. Original asset preserved.
- **Copy and content:** concise exam-library introduction, real catalogue titles
  and clear actions. Unnecessary Aura screenshot caption removed. Retired
  references are confined to the exam hub; current homepage links remain.

## Comparison history

1. **P2 — shield fidelity:** initial generic shields did not follow the existing
   certification-pathway artwork. Reused the pathway asset and Fluent tier stars,
   then refined its border, ribbon and shading with ImageGen. Final focused and
   full-view captures show the shared artwork in both consumers.
2. **P2 — badge-label contrast:** dark Azure and light Security labels were below
   4.5:1. Adjusted their foreground tokens; measured results now pass both themes.
3. **P2 — empty navigation entries:** hidden families remained in Contents.
   Updated visibility-aware navigation; browser checks confirm exact parity.
4. **P2 — Expert star alignment:** horizontal stars did not follow the reference's
   pointed arrangement. Lowered only the centre star; geometry checks and focused
   captures show the V shape at 390 and 1280px in both themes.
5. **P2 — ribbon code too low:** code sat below the ribbon centre. Anchored hub
   text to 46% with a half-height offset and adjusted pathway label offsets at
   desktop/mobile sizes. Revised focused captures show centred codes.

## Interaction and accessibility verification

- Ten hub viewport/theme cases and six homepage cases passed all subject filters,
  visible section counts, Contents updates, search, navigation and overflow.
- Filter symbols are decorative and retain text labels; controls are at least
  44px tall. Keyboard activation and visible focus pass.
- Retired native disclosure opens/closes using Enter/Space. Five references
  remain reachable; study guides are outside the disclosure.
- No-JavaScript view retains 30 current cards, five families, guides and all five
  retired references. Reduced motion is respected.
- No JavaScript errors or failed local resource requests in the responsive run.
  Focused pathway runs emitted an existing unused-preload warning; the contrast
  measurement helper emitted Canvas readback performance warnings. Neither is a
  visual or functional failure.
- Generated UI, counts, static versions, search, SEO, CSS bundle and performance
  checks pass. Existing CI contracts remain in place.

## Implementation checklist

- [x] Shared polished shield and correct tier stars.
- [x] Expert centre star follows the point.
- [x] Ribbon codes centred at both scales.
- [x] Visual filters and empty-section removal.
- [x] Current-only homepage and concise caption treatment.
- [x] Responsive, keyboard, contrast and no-JavaScript verification.

## Related-certification and homepage extension

Added compact shared badges to every homepage finder card, including the
expanded 24-card set, and single-certification related links on exam and guide
pages. Existing descriptions, counts and destinations are preserved.

Source references:

- Related cards: `/var/folders/dz/dyy7dm995kz71qsjqhv24mq80000gn/T/codex-clipboard-2c491ecd-94b5-463b-ae87-8b8552548d3b.png` — 1838×1396.
- Homepage finder: `/var/folders/dz/dyy7dm995kz71qsjqhv24mq80000gn/T/codex-clipboard-3b5939c7-2874-44eb-9a36-3b2b4844dd37.png` — 2246×1848.

Post-fix full-view evidence in the same visualization directory:
`related-certifications-light-1280.png`, `related-certifications-dark-390.png`,
`guide-related-certifications.png`, `homepage-exam-badges-light-1280.png` and
`homepage-exam-badges-light-390.png`. Source and rendered captures were viewed
together to assess hierarchy, compact badge scale and complete descriptions.

**P2 iteration:** two-column phone finder cards left too little space for the
badge and title. Changed phones to one column and intermediate widths to two.
Post-fix browser checks cover 320, 390, 768 and 1280px in both themes: 40 related
exam/guide cases and eight homepage cases passed, with no document/card overflow
or JavaScript errors. All 30 expanded homepage badges and filtering are verified.
Keyboard focus and a related-certification navigation target also pass.

The shared helper renders badge codes decoratively while existing link text
supplies the accessible code. The editorial similarity ratchet and its baseline
are unchanged and pass; no authored related-card text was modified. No new
fidelity findings remain.

## Final heading, level labels and current pathways

The shared v3 artwork now reads `Microsoft` / `CERTIFIED` in white on a navy upper
face, using the supplied Microsoft shield reference. Small `ASSOCIATE` and
`EXPERT` overlays sit above the stars in the blue field; the ribbon remains
centred and the Expert stars keep their pointed arrangement.

Source reference: `/var/folders/dz/dyy7dm995kz71qsjqhv24mq80000gn/T/codex-clipboard-774cbe8c-337c-4079-99fc-916685204d91.png`.
Full-view evidence: `homepage-certified-light-1280.png`,
`azure-certified-cards-light.png` and `related-certified-dark-390.png`.
Focused evidence: `expert-certified-light-1280.png`,
`finder-certified-light-390.png` and `pathway-certified-light-1280.png`.
Source and rendered captures were opened together for comparison.

Twelve page/viewport/theme checks cover the home finder, hub and AZ-104 related
and pathway surfaces at 390 and 1280px, light and dark. Tier overlays do not
overlap ribbons or stars; pathway hover moves all layers together. No document
overflow, JavaScript errors or failed local resource requests. The final artwork
is a 16,734-byte transparent WebP exported from built-in ImageGen; the exact
production prompt and export are recorded in `Tools/CERTIFICATION-SHIELDS.md`.

**P2 iteration:** a whitespace-sensitive pathway matcher initially omitted some
level overlays. Corrected it and verified the final 138 eligible pathway chips have exactly
one direct tier label. The generator is idempotent.

Retired exams are removed from all pathway diagrams using catalogue lifecycle
data. Obsolete destinations remove their whole route; surviving alternatives
keep correct connectors without dangling “or” markers. The DevOps route now
shows AZ-900 → AZ-104 → AZ-400 → DevOps Engineer Expert. The AI-300 heading now
describes the current ML Operations path. Reference pages and retired hub cards
are preserved. Evidence: `current-devops-path-light.png` and
`current-devops-phone-dark.png`, compared with the supplied DevOps screenshot.

Final result: passed

## WCAG readability and usability review

The detailed findings, measurements and limits are in `accessibility-audit.md`.
The review includes reading, search, filters, practice, FAQs, text enlargement,
legal/support pages, high-contrast states and the video preview.

axe-core 4.13.0 reports zero A/AA violations across 85 Chromium page/theme/width
cases, four Chromium interactive states and 36 WebKit cases (125 total).
Keyboard checks pass forward/backward search traversal, focus containment/return,
filters, grading and FAQ expansion. All 27 reflow/text-spacing/200% text cases pass.
WebKit refers to installed engine revision 2358 rather than the Safari app.

The follow-up fixes strengthen purple exam buttons, pathway credential labels,
small light-mode text, guide links and warm roadmap labels. Rendered-background
measurements supplement the unresolved automated gradient checks. WebKit search
now advances through every visible control, including disclosures, and excludes
hidden links in closed disclosures so Tab cannot stall at their summary. Forced-colour
matches use system highlight colours, and selected filters retain thicker borders
and heavier text. Twelve page/palette/width cases were checked in Chromium.

Video disclosure/play/focus transfer pass in WebKit. The external video has a
visible English (United Kingdom) track and a 15-cue en-GB transcript. Presence is
verified; audio accuracy, timing and audio-description coverage remain untested.

Accepted evidence includes the six numbered flow captures, before/after purple
button and guide-link images, WebKit reading/search, both forced-colour search
palettes, graded practice and the final roadmap. Each was opened and inspected.
The temporary capture of a practice card obscured by a modal was rejected and
replaced after verifying the dialog was closed.

Current-pathway validation also passed 36 route/width/theme cases across nine
affected pages, with no retired stations, empty routes, dangling alternatives,
document overflow or JavaScript errors. The similarity ratchet excludes only the
exact shared skip-link component; an injected-prose fixture verifies that the
markers cannot hide editorial text. Baseline and tolerance remain unchanged.

All 22 site checks pass locally, plus `git diff --check`. Native screen readers,
Safari/Firefox, physical-device zoom and complete media review remain outstanding.
The sampled flows pass; full WCAG conformance is unverified. PR46 is unpublished.
