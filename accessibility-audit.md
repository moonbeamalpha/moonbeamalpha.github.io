# Azure Mastery accessibility review — 1 October 2026

The PR46 build now has clearer text and controls in both themes, reliable modal
keyboard navigation in Chromium and WebKit, and readable search matches in
forced-colour mode. The 125 normal-theme axe-core scans report zero WCAG A/AA
violations. This review does not establish complete WCAG conformance.

## Scope and method

Reviewed the local PR46 build against [WCAG 2.2 AA](https://www.w3.org/WAI/WCAG22/quickref/),
using actual site theme preferences and matching browser colour preferences.
axe-core 4.13.0 checks WCAG 2.0, 2.1 and 2.2 A/AA tags:

- Chromium: 62 published pages in dark mode at 1280px, 14 representative
  templates in light mode at 1280px, and nine dark-mode pages at 390px.
- Chromium: four populated states — search, filtered finder, graded practice
  and an expanded FAQ.
- WebKit: nine representative routes at 390px and 1280px in both themes,
  totalling 36 scans. This is the installed WebKit engine (revision 2358),
  rather than the Safari application.

All 125 scans report zero violations. Unresolved checks remain recorded in the
raw results. Automated scans alone do not establish accessibility.

Keyboard checks cover skip navigation, search entry, arrow-key results, modal
traversal, Escape and focus return,
Space-activated filters, practice answers and FAQ expansion. Additional closed/expanded related-result checks verify
30 closed-state steps, then 30 forward and 30 backward expanded-state steps per
engine. Every keypress advances to a visible control: 14 distinct controls when
closed and 21 when expanded. This catches stalls that containment alone misses. WebKit's default
macOS keyboard behaviour uses Option+Tab to reach links outside the modal;
inside search, ordinary Tab now reaches every visible control.

Twenty-seven Chromium layout cases cover nine routes at 320px, 320px with WCAG
text spacing, and 200% text enlargement. No document overflow or offscreen
controls were found. The 320px check corresponds to the reflow width at 400%
zoom from 1280px; text enlargement doubles font sizes and leading. These are
layout simulations, rather than native browser zoom. Pathway rails and the
comparison table retain contained horizontal scrolling.

Additional checks cover 12 forced-colour page/palette/width combinations:
home, the exam hub and AZ-104, at 390px/1280px with light/dark system palettes.
Focused search, selected filters and graded practice were visually inspected.
These use Chromium emulation rather than a physical Windows installation.

## Reviewed flow

1. **Read and browse — improved.** Headings and body text remain clear in dark
   mode. Lightened purple download-button gradients and pathway credential
   labels; darkened light-mode small labels, guide links and roadmap labels.
   Evidence: `wcag-purple-cta-after.png`, `wcag-guide-link-after.png`,
   `wcag-roadmap-final-light.png`, `wcag-webkit-home-dark.png`.
2. **Search and choose an exam — passed after fixes.** Skip navigation, visible
   focus and keyboard filters work. Fixed a WebKit focus escape by advancing Tab
   through all visible modal controls, including disclosures. Hidden links in
   closed disclosures are excluded so traversal continues past the summary. High-contrast
   search matches use system Highlight/HighlightText colours; selected filters
   retain heavier borders and text when backgrounds are overridden. Evidence:
   `wcag-02-search-focus.png`, `wcag-webkit-search-dark.png`,
   `wcag-forced-search-dark.png`, `wcag-forced-search-light.png`.
3. **Practise and read FAQs — passed in sampled flows.** Answers and grading work
   by keyboard. Feedback explicitly identifies “Your answer” and “Correct
   answer” in high contrast. Eight links formerly nested in FAQ summary controls
   now sit in their answers. Evidence: `wcag-03-practice-keyboard.png`,
   `wcag-04-faq-keyboard.png`, `wcag-forced-practice-dark.png`.
4. **Enlarge text and use a narrow screen — passed in sampled layouts.** The
   homepage navigation wraps and grows with its content, keeping Download
   reachable at 200% text size. Focus scroll margins account for sticky controls.
   Reflow/text-spacing checks passed on nine routes. Evidence:
   `wcag-05-text-200.png`, `wcag-06-reflow-320.png`.
5. **Read support and legal information — improved.** Persistent prose-link
   underlines provide identification beyond colour. The support preview badge
   and light-mode legal links have stronger contrast. Evidence:
   `wcag-08-legal-dark.png`, plus support/privacy/terms scan and layout results.
6. **Watch the Aura preview — partially verified.** The disclosure and Play
   button work by keyboard, and focus transfers to the titled video iframe.
   The external YouTube fallback remains available. YouTube visibly offers
   English (United Kingdom) captions; a timestamped en-GB export contains 15
   cues. Caption accuracy, synchronization and audio-description coverage were
   not checked. Evidence: `wcag-07-video-keyboard.png`,
   `wcag-video-keyboard.json`, `wcag-caption-verification.json`.

## Findings addressed

| Finding | WCAG criteria | Change / measured result |
|---|---|---|
| Light cyan labels at 4.42:1; legal links at 4.31:1 | 1.4.3 Contrast (Minimum) | Darker accents; cyan measured at 4.87:1 |
| Dark legal links differed from nearby text by only 2.76:1 | 1.4.1 Use of Color | Persistent prose-link underlines |
| White support badge text on blue at 3.01:1 | 1.4.3 | Deeper blue; 5.61:1 |
| Purple exam download buttons fell to 4.00:1 over the rendered gradient | 1.4.3 | Lighter end stop; sampled button text now at least 5.78:1 |
| Small credential labels on warm pathway chips fell to 4.30:1 | 1.4.3 | Brighter dark-mode labels; sampled role text at least 4.93:1 |
| Light-mode guide-library links measured 1.38:1 | 1.4.3 | Theme-aware link colour; sampled guide actions at least 5.06:1 |
| Light-mode exam-format labels measured about 4.43:1 | 1.4.3 | Darker muted token; sampled labels at least 4.78:1 |
| Light-mode GitHub roadmap labels measured 4.41:1 | 1.4.3 | Deeper warm accents; sampled featured roadmap labels at least 4.82:1 |
| WebKit search focus could escape; hidden related links could stall Tab | 2.1.1 Keyboard; 2.4.3 Focus Order | Explicit forward/backward navigation through all visible modal controls |
| Search matches became hard to read in forced colours | 1.4.3; 1.4.1 | System highlight colours; selected filter borders/weight remain distinct |
| Search-field edges were difficult to distinguish | 1.4.11 Non-text Contrast | Border measured at 4.22:1 dark / 4.37:1 light |
| Shared navigation lacked bypass and consistent focus | 2.4.1; 2.4.7; 2.4.11 | Skip link, focusable main target, outlines and scroll margins |
| FAQ summaries nested another interactive control | 2.1.1; 4.1.2 Name, Role, Value | Links moved into answers, preserving wording |
| Download fell outside the enlarged-text header | 1.4.4 Resize Text | Wrapping navigation with content-driven height |

The [normal-text contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
is 4.5:1; large text requires 3:1. Ratios above are rounded for reporting only;
pass/fail decisions use unrounded values. Representative dark body text measures
5.86:1 on cards and muted text 5.06:1. The main white Download label measures at
least 5.98:1 at the checked gradient endpoints. Decorative certification artwork
repeats information available in the accompanying card text.

## Evidence and limits

Accepted screenshots were saved, opened and visually inspected. Evidence resides
in `/Users/chris/.codex/visualizations/2026/10/01/01a0f69c-0d3c-77c0-a7a8-6c5308854827/`.

- `wcag-page-scans.json`, `wcag-interactive-states.json`, `wcag-webkit-checks.json`.
- `wcag-keyboard-layout.json`, `wcag-forced-colours.json`.
- `wcag-search-traversal-chromium.json`, `wcag-search-traversal-webkit.json`.
- `wcag-rendered-gradient-contrast-after.json`, `wcag-roadmap-rendered-contrast.json`.
- `wcag-video-keyboard.json`, `wcag-caption-verification.json`.

Gradient review combines CSS foreground/endpoint measurements with sampled
rendered backgrounds after temporarily hiding text in the browser. Hidden
content and decorative symbols are not treated as readable-text failures.
Rectangle samples can include rounded badge corners; those candidates require
checking the actual text background before classification. The Aura launch
badge already uses the accessible shared gradient and needed no additional fix.
Background-only measurement images are diagnostic data, not UI screenshots.

Many gradient, pseudo-element and image-text nodes remain unresolved by axe.
Full coverage of those surfaces is not established. The closed search dialog
also produces an unresolved ARIA reference check; populated IDs and focus
behaviour were checked separately. In forced colours, axe can compare authored
CSS colours with system-painted backgrounds and report misleading contrast
results; the forced-colour conclusions here come from rendered inspection and
system-colour checks, separate from the 125 normal-theme scans.

VoiceOver/NVDA announcements, native Safari/Firefox, physical-device zoom and
complete media accessibility remain unverified. The caption track's presence
is established, but [caption completeness](https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html),
audio accuracy, timing and coverage of meaningful visual information need a
separate playback review before claiming full conformance.

All 22 site CI checks pass locally, plus `git diff --check`. The changes remain
in PR46 and have not been merged or published.
