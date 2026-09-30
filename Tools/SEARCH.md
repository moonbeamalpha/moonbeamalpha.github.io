# Azure Mastery site search

The shared search controller and styles run directly on GitHub Pages. There is
no server API, dependency bundle, search telemetry or stored query history.
Opening the dialog or entering a query loads the same-origin index once. The
index, controller and stylesheet use content-hashed URLs; the image/font service
worker does not intercept them.

## Maintaining content

Run these in order after editing published content or adding a page:

```sh
python3 Tools/build-search-index.py
python3 Tools/sync-search-ui.py
python3 Tools/version-static-assets.py
python3 Tools/update-sitemap-lastmod.py
python3 Tools/build-search-index.py --check
python3 Tools/sync-search-ui.py --check
python3 Tools/test-search-index.py
node Tools/test-search.mjs
```

Run the remaining marketing CI gates too. For shared UI changes that require
exam structured-data dates to advance, update the relevant
`SEO_UPDATED_OVERRIDES` and run `Tools/optimise-marketing-seo.py --dates-only`.
That mode uses the existing date generator without reading private banks or
regenerating question previews. Editorial guide dates remain tied to guide
content, rather than shared navigation changes.

Discovery comes from the sitemap, scoped to Azure Mastery. Exam titles and
retirement dates come from the committed catalogue snapshot; successor routes
come from existing SEO lifecycle metadata. New sitemap pages are automatically
indexed. The generator fails when files, homepage feature anchors, lifecycle
metadata or the 150 KiB gzip budget disagree.

Index content includes titles, descriptions, subjects, primary headings,
objectives, exam overviews, traps and study plans, plus guide and information-page
content. It excludes navigation, footers, decorative content, duplicated product
benefits, conversion bands, exam FAQ blocks, question previews, certification
rails, related-page cards and the search UI itself. Homepage feature results link
directly to their existing section anchors.

## Matching and interaction

Code punctuation, spaces, case and accents are normalized. Title matches rank
above subjects/headings, descriptions and body text; an exact exam code ranks
its own exam page first. Multiword queries require every non-stopword term.
Partial words match prefixes. Numeric tokens are never corrected. Alphabetic
tokens of at least five characters accept one insertion, deletion, replacement
or adjacent transposition only when exact/prefix matching returns no results.
Common aliases include PowerBI, M365, Entra ID, Azure AD, MLOps and networking.
Current pages precede retired references for broad subject queries; exact old
codes remain findable with lifecycle and successor labels.

All / Exams / Guides / Pages filters use the same matcher in the modal and inline
search. Results appear in batches of eight. Enter in the search field focuses
the first result; Enter on a result follows its link. Arrow keys move through
results, and Tab traverses ordinary links and controls. Escape closes the native
dialog and restores focus. The dialog explicitly wraps Tab at its boundaries.
The keyboard shortcut does not interrupt typing in editable controls.

Queries and highlighted excerpts use DOM text nodes, never HTML interpolation.
Requests time out after 12 seconds and failures can be retried. Input revisions
prevent stale async responses from replacing a newer query or clear action.
Mobile viewport resize events keep the panel inside the visible keyboard area.
Search controls remain hidden if the controller cannot initialize; ordinary
exam and guide navigation remains available.

## Validation on 30 September 2026

- Python contracts: discovery, deterministic freshness, anchors, exclusions,
  catalogue/lifecycle parity, unique IDs, versioned assets and UI idempotence.
- Node contracts: code variants, unknown codes, exact ranking, title prefixes,
  subjects, aliases, misspellings/transpositions, multiword matching, type
  filters, successor routes, excerpts and index budget. Measured p95 about 1ms
  on the local Node runtime against 68 destinations; index 142,437 bytes gzip.
- Browser: header controls at 320, 430, 768, 1024 and 1440 CSS pixels across the
  homepage, exam hub, AZ-104, GH-900, guides hub, About, Support and Privacy.
  No search/header controls escaped the viewport in 40 checks.
- Browser interactions: native dialog, Escape/focus return, shortcut, Tab
  wrapping, result navigation, filters, 8-to-16 pagination, clear/no-results,
  inline results, dark/light themes and same-page feature navigation.
- A separate local fixture server tested loading/clearing before completion,
  HTTP failure/retry, unsupported index versions, literal HTML-like result text
  and browsing with document scripts removed. Fixtures are outside the published
  repository.
- Mobile layouts and reduced visible viewport heights were checked in the
  desktop browser. A 640 × 360 CSS-pixel viewport checked reflow equivalent to
  200% zoom on a 1280 × 720 viewport. Search has no entrance animation and its
  reduced-motion rule disables inherited transitions and animations. Physical
  iPhone keyboard, actual browser zoom, OS motion-preference emulation and
  VoiceOver testing remain manual checks; these browser tests do not establish
  those device results.

All existing marketing CI commands were also run locally. No baseline or
advertised count was changed. Publishing remains a separate owner decision.
