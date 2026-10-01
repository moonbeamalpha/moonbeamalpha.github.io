# Azure Mastery accessibility review — 1 October 2026

The proposed site changes improve dark-mode readability and keyboard use. The
final axe-core scans report zero WCAG A/AA violations. This is an implementation
review against [WCAG 2.2 AA](https://www.w3.org/WAI/WCAG22/quickref/), not a claim
of complete conformance: automated contrast checks leave gradient-backed text
unresolved, and screen-reader and media testing remain outstanding.

## Scope and method

Reviewed the local PR46 build using Chromium, actual light/dark theme settings
and the matching OS colour preference. Automated checks use axe-core 4.13.0 with
WCAG 2.0, 2.1 and 2.2 A/AA tags:

- 62 published pages in dark mode at 1280px.
- 14 representative page templates in light mode at 1280px.
- Nine representative pages in dark mode at 390px.
- Four populated interactive states: search, filtered finder, graded practice
  and an expanded FAQ.

All 89 scans report zero violations. Keyboard checks cover skip navigation,
search entry, arrow-key results, 25 Tab cycles inside the modal, Escape and focus
restoration, Space-activated subject filters, practice answers and FAQ expansion.

Twenty-seven layout cases cover nine routes at 320px, 320px with WCAG text
spacing, and 200% text enlargement. No document overflow or offscreen controls
were found. The 320px check tests the reflow width corresponding to 400% zoom
from 1280px; the enlargement check doubles text sizes and leading. These are
layout simulations, not native browser-zoom certification. Pathway rails and
the comparison table retain their intentional contained horizontal scrolling.

## Reviewed flow

1. **Read and browse.** The homepage, exam hub, detail pages and Aura page retain
   clear headings and readable body text in dark mode. Strengthened search-field
   borders and corrected low-contrast light-mode accents. Evidence:
   `wcag-after-home.png`, `wcag-after-exams-.png`,
   `wcag-after-exams-az-104-.png`, `wcag-after-ask-aura-.png`.
2. **Search and choose an exam.** Added a first-focus “Skip to content” link,
   consistent focus outlines and proper grouping for search suggestions. Search
   contains focus, supports arrow navigation and restores focus when dismissed;
   filters work with the keyboard. Evidence: `wcag-01-skip-focus.png`,
   `wcag-02-search-focus.png`.
3. **Practise and read FAQs.** Answer controls work with keyboard activation;
   feedback includes explicit “Your answer” and “Correct answer” labels.
   Removed eight links nested inside FAQ summary controls across six pages;
   their destinations remain in the answers. Evidence:
   `wcag-03-practice-keyboard.png`, `wcag-04-faq-keyboard.png`.
4. **Enlarge text and use a narrow screen.** The homepage navigation now wraps
   and grows with its content, keeping Download reachable at 200% text size.
   Focus scroll margins account for sticky navigation. Reflow and text-spacing
   checks passed on the nine sampled routes. Evidence: `wcag-05-text-200.png`,
   `wcag-06-reflow-320.png`.
5. **Read support and legal information.** Underlined prose links so dark-mode
   readers can identify them without relying on colour. Darkened the support
   preview badge and light-mode link colour to meet normal-text contrast.
   Evidence: automated and layout results for privacy, support and terms.

## Findings addressed

| Finding | WCAG criteria | Change |
|---|---|---|
| Light cyan labels at 4.42:1; legal links at 4.31:1 | 1.4.3 Contrast (Minimum) | Darker light-mode accents; measured cyan now 4.87:1 |
| Dark legal links differed from surrounding text by only 2.76:1 | 1.4.1 Use of Color | Persistent underlines on prose links |
| White support badge text on blue at 3.01:1 | 1.4.3 | Deeper blue; now 5.61:1 |
| Search-field edges were difficult to distinguish | 1.4.11 Non-text Contrast | Stronger border; 4.22:1 dark and 4.37:1 light against the surrounding card |
| Shared navigation lacked a keyboard bypass and consistent focus treatment | 2.4.1 Bypass Blocks; 2.4.7 Focus Visible; 2.4.11 Focus Not Obscured | Focusable main destination, visible skip link, outlines and scroll margins |
| FAQ summaries nested another interactive control | 2.1.1 Keyboard; 4.1.2 Name, Role, Value | Link moved to the answer, preserving visible wording |
| Download fell outside the enlarged-text header | 1.4.4 Resize Text | Wrapping navigation with content-driven height |

Representative dark-mode body text measures 5.86:1 on cards; muted text measures
5.06:1. The main white download label measures at least 5.98:1 at the checked
gradient endpoints. These exceed the normal-text 4.5:1 minimum. Important actions
retain text labels; decorative certification tier artwork repeats information
available in the card text.

## Evidence and remaining verification

Screenshots were opened and visually inspected after capture. Evidence resides
in `/Users/chris/.codex/visualizations/2026/10/01/01a0f69c-0d3c-77c0-a7a8-6c5308854827/`.
The saved results are `wcag-page-scans.json`, `wcag-interactive-states.json` and
`wcag-keyboard-layout.json`. The page scan lists both violations and checks
requiring human review rather than treating those checks as passes.

Many colour-contrast nodes remain unresolved by axe because of gradient
backgrounds. Key text colours, buttons and search boundaries were measured;
complete coverage of every gradient, pseudo-element and image-embedded label is
not established. The closed search dialog also produces an unresolved ARIA
reference check; the populated dialog, matching result IDs and keyboard focus
behaviour were checked separately.

VoiceOver/NVDA announcements, Safari/Firefox behaviour, forced-colour rendering,
physical-device zoom and video captions/audio descriptions were not tested.
Those checks are needed before describing the site as fully WCAG conformant.

The fixes are part of PR46 and have not been published.
