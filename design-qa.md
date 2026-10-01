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

Final result: passed
