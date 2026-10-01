# Certification shield artwork

The homepage exam finder, exam library, related-certification cards and certification pathways share
[`certification-badge-shield-v3.webp`](../exams/images/certification-badge-shield-v3.webp).
It is a refinement of the existing `certification-badge-shield.webp`, produced
with the built-in ImageGen edit tool on 1 October 2026. The original and the
intermediate v2 artwork are preserved.

## Production brief

Initial refinement: preserve the transparent square canvas, pointed navy shield,
broad white ribbon and Azure-blue lower face. Refine symmetry, perimeter, ribbon
edges and restrained shading; remove muddy edges and excessive shadow.

Final edit prompt (built-in ImageGen, transparent background):

> Edit the refined shield. Replace the single-line CERTIFICATION heading with
> exactly two centred lines: “Microsoft” and “CERTIFIED”. Use the supplied
> reference's navy upper face and white text. Microsoft is title case in clean
> bold sans-serif; CERTIFIED is smaller uppercase with modest letter spacing.
> Preserve the square canvas, shield shape and scale, navy perimeter, blank curved
> white ribbon, bright Azure-blue lower field, restrained shading and genuinely
> transparent outer background. Keep the ribbon and lower field blank for
> code-native exam, tier and star overlays. Do not copy the reference's exam
> titles, tier text or stars. Do not add a four-square logo, ornaments, external
> shadow or additional text. Make only the upper-face colour and heading change,
> with sharp polished edges at small icon sizes.

## Export and overlays

The 1,254px transparent PNG was resized proportionally to 300×300 with Lanczos
resampling and exported as WebP, quality 92, method 6. The final result is 16,734 bytes.
Only export conversion and resizing happened outside ImageGen.

Each card retains its exam code as accessible link text; the badge repeats it
decoratively in the centred white ribbon. Pathway codes remain real text. Tier stars use the
existing Fluent star asset: one for Fundamentals, two for Associate and three
for Expert. Small `ASSOCIATE` and `EXPERT` labels appear above the corresponding
stars in the blue field. Fundamentals and retired references omit these labels.
The Expert centre star sits lower to follow the shield's point.
All consumers use the same versioned asset so cached images cannot retain the
old artwork after publication.

Cards and pathways were checked at phone and desktop widths in light and dark
themes. The ribbon labels and stars remain legible and aligned at both scales.
