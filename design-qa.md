# Certification Pathway Shield and Tier Design QA

**Source visual truth**

- Shield geometry reference: `/tmp/codex-remote-attachments/01a015aa-3843-7d50-ba1d-8591b072d240/AC13654B-EC18-4845-BC94-FF388C6EAFAE/1-Pasted-Image-1.jpg`
- Tier and ribbon-alignment reference: `/tmp/codex-remote-attachments/01a015aa-3843-7d50-ba1d-8591b072d240/3EC37F19-B5AD-470A-AE2F-038FEAC36835/1-Pasted-Image-1.jpg`
- Latest reference pixels: 1200 × 628.
- Target characteristics: centred ribbon labels; one star for Fundamentals, two for Associate, and three for Expert; compact badges that stay on one pathway row.

**Rendered implementation evidence**

- Desktop tier view: `/Users/chris/.codex/visualizations/2026/08/18/01a015aa-3843-7d50-ba1d-8591b072d240/certification-tiers-final-desktop.png`
- Mobile tier view: `/Users/chris/.codex/visualizations/2026/08/18/01a015aa-3843-7d50-ba1d-8591b072d240/certification-tiers-final-mobile.png`
- Light-theme tier view: `/Users/chris/.codex/visualizations/2026/08/18/01a015aa-3843-7d50-ba1d-8591b072d240/certification-tiers-final-light.png`
- Source/implementation comparison: `/Users/chris/.codex/visualizations/2026/08/18/01a015aa-3843-7d50-ba1d-8591b072d240/certification-tier-comparison.png`
- Desktop viewport override: 1440 × 1000 CSS px; browser content capture: 1425 × 990 px.
- Mobile viewport override: 390 × 844 CSS px; browser content capture: 375 × 812 px.
- State: AZ-305 pathway showing Fundamentals, Associate, and Expert tiers. Dark, light, and mobile responsive states were checked.

## Findings

- No actionable P0, P1, or P2 differences remain.
- The generic `CERTIFICATION` crest label was enlarged and strengthened after live-scale review. It is now visibly legible at both the 82 px desktop and 76 px mobile badge sizes while leaving clear space around the word.

## Required Fidelity Surfaces

- **Ribbon alignment:** Every non-outcome exam code is horizontally centred in its 112 px desktop / 104 px mobile chip. The code is optically lifted by 1 px so its baseline sits on the curved ribbon midpoint; hover lifts both shield and label together by a further 3 px.
- **Tier language:** The starless 300 × 300 transparent WebP base combines with the official Microsoft Fluent UI filled-star icon. Fundamentals uses a 12 px strip, Associate 27 px, and Expert 42 px, producing one, two, and three evenly spaced stars.
- **Typography:** Exam codes remain accessible HTML text using the existing site type system at 11 px / 800 weight on desktop and 10.5 px on mobile. The asset contains no Microsoft wordmark or endorsement claim.
- **Spacing and layout rhythm:** A browser sweep covered 31 exam pages, 231 certification chips, and 91 pathway rails. All desktop and mobile rails remain `nowrap`; 48 longer mobile rails use their contained horizontal scroll, with no document-level overflow.
- **Colours:** Supporting badges retain their violet/blue treatment and the current exam retains its brighter cyan/blue glow. White tier stars stay clear in dark and light themes.
- **Asset quality:** The final shield is a true-alpha 10 KB WebP with no baked checkerboard, green spill, or star. The reusable Fluent SVG supplies the tier markers at browser-native sharpness.
- **Content integrity:** Existing exam codes, role labels, pathway tags, outcome copy, and navigation targets are unchanged. The level comes from the app certification taxonomy, with legacy DP-203 and DP-600 retained as Associate.

## Full-view Comparison Evidence

- The combined comparison confirms the reference's one/two/three-star progression is immediately legible in the implementation.
- Ribbon labels are centred independently of star count, unlike the previous badge asset where a baked-in star limited every exam to the same visual level.
- The implementation deliberately adapts the source to the Azure Mastery design system: compact pathway rails, generic `CERTIFICATION` crest copy, live exam-code text, and a separate credential outcome card.
- No shields, labels, arrows, or cards are clipped on desktop. Mobile preserves the complete sequence on one internally scrollable row.

## Validation Evidence

- Browser desktop audit: 31 pages, 231 certification chips, 91 rails, zero issues.
- Browser mobile audit: 31 pages, 231 certification chips, 91 rails, 48 contained scroll rails, zero issues.
- Browser console: zero warnings or errors in the final preview session.
- Static validator: 33 exam pages and 9 guide pages passed, including exact per-code tier checks.
- `git diff --check`: passed.

## Comparison History

1. The original rectangular pathway chips were replaced by compact peaked shields with protruding curved ribbons.
2. The first refined raster used one baked-in star, which could not express the actual certification level.
3. The lower star was removed from the generated shield and its blue gradient reconstructed. A separate Fluent icon now renders the tier count.
4. The exam code moved from `translateY(2px)` to `translateY(-1px)`, matching the ribbon's optical centre.
5. The star scale was increased after browser review so the tier difference remains obvious at normal page zoom without crowding the badge.
6. The crest label was enlarged and changed to a stronger semibold treatment after user feedback that the original `CERTIFICATION` text was too small.

## Implementation Checklist

- [x] Use a real reusable shield asset rather than a CSS-drawn badge.
- [x] Use a real icon-library star rather than text symbols or CSS art.
- [x] Keep the exam code as accessible HTML text.
- [x] Render one, two, or three stars from the canonical certification level.
- [x] Validate the exact tier on every exam-code chip.
- [x] Preserve single-row desktop pathways across all exam pages.
- [x] Preserve contained mobile scrolling without page overflow.
- [x] Verify dark, light, desktop, and mobile states.
- [x] Verify browser-console and static-validator health.

final result: passed
