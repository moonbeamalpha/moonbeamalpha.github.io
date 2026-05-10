# SEO Phase 2 — Handoff Document

**Audience:** the next Claude Code session that picks up this work.
**Status:** Phase 1 shipped on 2026-05-08 via PR [#2](https://github.com/moonbeamalpha/moonbeamalpha.github.io/pull/2). Phase 2 has **not** started.
**Owner:** Chris (Moonbeamalpha) — solo founder of Moonbeam Alpha Ltd, builder of [Azure Mastery](https://azuremastery.app/) (App Store ID 6760594569).

---

## Read this entire document before touching the repo

You are a fresh Claude Code instance with no memory of Phase 1. The brief below replaces that context. The hard rules in §3 are non-negotiable.

---

## 1. What Phase 1 already did (do not redo)

PR #2 (commit `3aa1ef3`, merge `f94720f`) shipped these changes to `main`:

- **`apps/AzureMastery/index.html`**
  - Added a `.sr-only` utility class to the inline `<style>` block (typography section, near the `display-*` definitions).
  - Inserted a visually-hidden `<h1 class="sr-only">` carrying the brand + Tier 1 cert codes (AZ-104, AZ-900, AZ-305, AZ-204, AZ-400 + "and 17 more"). Demoted the visible "Know When You're Ready." element from `<h1>` to `<h2>` (visual unchanged because styling is on `display-large hero-headline`).
  - Removed the `aggregateRating` block from JSON-LD. It was set to `ratingValue: 5, ratingCount: 1` — below the ≥3 threshold needed to avoid Google's structured-data spam classifier. An HTML comment above the `<script>` tag records the removal date and the re-add condition.
- **`index.html` (root)**
  - Cleaned up the meta-refresh: target now `/apps/AzureMastery/` (clean trailing-slash form, not `index.html`).
  - Widened the `<title>` to `Azure Mastery — AI-Powered Azure Certification Exam Prep`.

Live site verified post-merge: 1 H1 with cert codes, no `"aggregateRating"` JSON field, root URL serves and redirects.

**Do not redo any of these.** If you find yourself touching the H1 or the `aggregateRating` JSON-LD block, you are off-task.

---

## 2. What Phase 2 is

Build five per-exam landing pages — Tier 1 only — at `/exams/<cert>/`. Each page targets cert-specific Google queries ("AZ-104 study app", "AZ-900 practice questions iOS", etc.) that the homepage cannot rank for because of keyword dilution.

Tier 1 (build in this order):

1. **AZ-900** (Microsoft Azure Fundamentals) — easiest, lowest stakes, smallest content load. Ship first.
2. **AZ-104** (Microsoft Azure Administrator) — highest search volume, biggest payoff.
3. **AZ-305** (Microsoft Azure Solutions Architect Expert) — flagship architect cert.
4. **AZ-204** (Microsoft Azure Developer Associate) — developer track.
5. **AZ-400** (Microsoft Azure DevOps Engineer Expert) — DevOps track.

Tier 2/3/4 (the remaining 17 of 22 certs) are **out of scope for Phase 2**. Once Tier 1 is live and indexing, that's a separate Phase 2.5 conversation.

### 2.1 URL structure

- Pages live at `/exams/<cert-code-lower>/index.html` so the canonical URL is `https://azuremastery.app/exams/<cert-code-lower>/`.
- Trailing-slash directory paths only. No `.html` files in URLs.
- Examples: `/exams/az-104/`, `/exams/az-900/`, `/exams/az-305/`.

### 2.2 Pre-work (do this first)

The homepage's CSS is ~80KB inlined. Stamping that into 5 cert pages would balloon the repo. Cert pages are text-heavy and don't need most of the homepage's animation/component styles.

**Step 1:** Create `exams/styles.css` (~10–15KB) containing only:

- The `:root { --azure-cyan ... }` custom properties (verbatim copy, so brand colors match).
- Typography classes (`display-*`, `heading-*`, `body-*`, `label-eyebrow`, `headline-accent`).
- Basic layout: `body`, `main`, `section` defaults; container/max-width rules.
- Simple link/button base styles (`.btn-primary`, `.btn-ghost` — abridged, no GSAP-driven hover effects).
- A simple single-column or two-column container.
- The `.sr-only` utility from Phase 1.

Do **not** copy: hero composition, scroll animations, fade-up GSAP rules, screenshot card styles. Cert pages don't need them. Keep the file plain CSS — no preprocessor, no CSS-in-JS, no framework.

### 2.3 Page template

Create `exams/_template.html` (a reference file, **not** linked from the sitemap or any nav). Each cert page copies it and substitutes variables.

Variables (lowercase = path-safe, uppercase = display):

| Variable | Example for AZ-104 |
|---|---|
| `{{cert-code-lower}}` | `az-104` |
| `{{CERT_CODE}}` | `AZ-104` |
| `{{CERT_NAME}}` | `Microsoft Azure Administrator Associate` |
| `{{Q_COUNT}}` | (from app data — Chris confirms per cert; see §5) |
| `{{MS_LEARN_URL}}` | `https://learn.microsoft.com/en-us/credentials/certifications/azure-administrator/` |
| `{{EXAM_FORMAT}}` | `40–60 questions, 100 min, USD $165, 2-year validity` (Chris confirms current values from MS Learn) |
| `{{OBJECTIVES}}` | Array of `{ name, weight, summary }` from the official skills outline |
| `{{FAQS}}` | Array of `{ question, answer_html }` ≥5 items |
| `{{STUDY_PLAN_HTML}}` | Cert-specific 1–4 week study plan |

Skeleton (full template should look like this):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{CERT_CODE}} Study App — {{CERT_NAME}} Practice Questions on iOS | Azure Mastery</title>
  <meta name="description" content="Pass {{CERT_CODE}} ({{CERT_NAME}}) with confidence. Azure Mastery is an iOS app with {{Q_COUNT}}+ {{CERT_CODE}} practice questions, AI score prediction, and adaptive study plans. Free download.">
  <link rel="canonical" href="https://azuremastery.app/exams/{{cert-code-lower}}/">
  <meta name="apple-itunes-app" content="app-id=6760594569">
  <link rel="stylesheet" href="/exams/styles.css">
  <!-- OpenGraph + Twitter Card pattern from apps/AzureMastery/index.html, with cert-specific title + description -->
  <!-- JSON-LD: SoftwareApplication scoped to this cert (subset of homepage's), plus FAQPage schema for the FAQs section -->
</head>
<body>
  <!-- Header: simple text-only nav (no GSAP). Brand link → /apps/AzureMastery/. -->
  <main>
    <h1 class="display-large">{{CERT_CODE}} Study App for iOS — {{CERT_NAME}}</h1>
    <p class="body-large"><!-- 40–80 word lead paragraph --></p>

    <section id="what-is-it">
      <h2 class="display-small">What is the {{CERT_CODE}} exam?</h2>
      <!-- 200–400 words. Cite MS Learn at {{MS_LEARN_URL}}. State exam format from {{EXAM_FORMAT}}. -->
    </section>

    <section id="objectives">
      <h2 class="display-small">{{CERT_CODE}} exam objectives</h2>
      <!-- Loop {{OBJECTIVES}}: each domain as <h3>{{name}} — {{weight}}</h3> + 60–120 word summary -->
    </section>

    <section id="how-azure-mastery-helps">
      <h2 class="display-small">How Azure Mastery helps you pass {{CERT_CODE}}</h2>
      <!-- 4–6 paragraphs. Cert-specific details: question count per domain, simulator config -->
    </section>

    <section id="study-plan">
      <h2 class="display-small">Suggested {{CERT_CODE}} study plan</h2>
      {{STUDY_PLAN_HTML}}
    </section>

    <section id="faqs" itemscope itemtype="https://schema.org/FAQPage">
      <h2 class="display-small">{{CERT_CODE}} FAQs</h2>
      <!-- Loop {{FAQS}}: each as <article itemscope itemtype="Question">…</article> -->
    </section>

    <section id="cta">
      <a class="btn-primary" href="https://apps.apple.com/gb/app/azure-mastery/id6760594569">Download Azure Mastery — Free</a>
    </section>

    <nav id="related" aria-label="Related certifications">
      <h2 class="display-small">Related Azure certifications</h2>
      <!-- 2–3 sibling cert links (e.g. for AZ-104, link to AZ-900 and AZ-305) -->
    </nav>
  </main>
  <!-- Footer: copy from homepage, but text-only -->
</body>
</html>
```

### 2.4 Per-page content non-negotiables

- ≥800 words of unique body copy per page. Below that, Google treats it as a thin doorway.
- Cert-specific objective list copied from the official `learn.microsoft.com/en-us/credentials/certifications/...` skills outline, with a link to that source page. **Do not paraphrase loosely** — Microsoft updates these and Google notices stale paraphrases.
- ≥5 FAQ Q&A items wrapped in `FAQPage` JSON-LD.
- Each page links to `/apps/AzureMastery/` + 2–3 sibling cert pages (topical cluster).
- No two pages share more than ~30% identical body content. The "How Azure Mastery helps" section can have 2–3 shared paragraphs of boilerplate; everything else is cert-specific.

### 2.5 Homepage update — "Browse by Certification"

Once at least 3 of the 5 Tier 1 pages exist, add a new section to `apps/AzureMastery/index.html`. Render the cert tag chips that already exist at lines ~1339–1361 as **links** to the cert page if one exists, plain spans otherwise.

Pseudocode:
```
For each chip:
  if /exams/<cert-lower>/index.html exists in the repo:
    render as <a href="/exams/<cert-lower>/" class="hero-exam-tag …">
  else:
    keep as <span class="hero-exam-tag …">
```

This gives the new pages internal-link equity from the strongest page on the site.

### 2.6 Sitemap update

After each cert page is added, append to `sitemap.xml`:

```xml
<url>
  <loc>https://azuremastery.app/exams/az-104/</loc>
  <priority>0.8</priority>
  <changefreq>monthly</changefreq>
</url>
```

Keep homepage at priority `1.0`. Submit the updated sitemap in Google Search Console after the batch lands.

---

## 3. Hard rules — non-negotiable

These come from Chris's original SEO planning document and the conversation that produced Phase 1. **Violating any of these is grounds for a revert.**

1. **Never commit, push, or merge without Chris's explicit approval.** Make all edits on a feature branch (e.g. `seo/phase-2-cert-pages`). Show the diff. Wait for sign-off. This applies even to changes that look "obviously correct."
2. **No new third-party scripts.** Existing `gtag.js` (G-YTN7LFS04Y), Google Fonts, and GSAP from cdnjs are grandfathered. Do **not** add analytics, tag managers, chat widgets, A/B SDKs, or anything else that loads external code.
3. **No fabricated data.** No fake ratings, ratingCount, testimonials, screenshots, or review numbers. If a structured-data field needs real data and it's not available, omit the field.
4. **No new build tooling.** No Jekyll, 11ty, Astro, Tailwind, Bootstrap, React. A static `.css` file linked via `<link rel="stylesheet">` is fine; build steps are not.
5. **Match the existing design system.** Reuse the classes from `apps/AzureMastery/index.html` (`display-large`, `display-small`, `heading-medium`, `body-large`, etc.) and the design tokens in `:root`. Don't restyle.
6. **UK English in copy** ("personalised", "optimised", "behaviour"). Cert codes stay in their official format.
7. **Mobile-first.** Test at 375px viewport (iPhone SE) before considering any UI change done.
8. **Verify before reporting "done".** Run the verification commands in §6 after each PR. Don't claim a page is shipped without `curl`-confirming it.

---

## 4. Critical files

Read these before editing:

- `apps/AzureMastery/index.html` — homepage. Source of truth for design tokens, typography classes, JSON-LD pattern. **Do not modify** for Phase 2 except for the §2.5 "Browse by Certification" addition.
- `index.html` (root) — meta-refresh redirect to the homepage. **Do not modify** for Phase 2.
- `sitemap.xml` — append new cert URLs only.
- `robots.txt` — already permissive; no changes needed.
- The plan document at `/Users/chris/.claude/plans/review-and-implement-the-magical-nest.md` (local to Chris's machine) covers the full reasoning. If you can read it, do; if not, this handoff is the source of truth.

Files Phase 2 will create:

- `exams/styles.css`
- `exams/_template.html`
- `exams/az-900/index.html`
- `exams/az-104/index.html`
- `exams/az-305/index.html`
- `exams/az-204/index.html`
- `exams/az-400/index.html`

---

## 5. Open items — you cannot start the cert pages without these

Ask Chris before writing any cert page content:

1. **Q_COUNT per cert**: how many practice questions does the app contain for AZ-900, AZ-104, AZ-305, AZ-204, AZ-400? He pulls these from app data.
2. **Per-cert app screenshots**: do per-cert UI captures exist? The "Suggested study plan" and "How Azure Mastery helps" sections are stronger with cert-specific screenshots than reusing the same generic ones across all 5 pages (Google will flag duplicate-content if every page has the same images).
3. **Google Analytics decision**: existing `gtag` conflicts with the SEO plan's "no tracking" rule. Chris needs to confirm: keep, remove, or supplement with Search Console only (server-side query data, no client-side tracking).
4. **Canonical strategy confirmed**: Phase 2 assumes the homepage stays canonical at `/apps/AzureMastery/` (Option B from Phase 1). If Chris decides to migrate the homepage to root (Option A), the cert page canonicals don't change but the internal-link strategy does — confirm before stamping pages out.

You **can** start the §2.2 styles.css extraction without these answers — it's pure CSS refactoring. Begin there.

---

## 6. Verification (run before merging each PR)

```bash
# 1. Sitemap is valid XML and resolves
curl -s https://azuremastery.app/sitemap.xml | xmllint --noout -

# 2. Every URL in sitemap returns 200
curl -s https://azuremastery.app/sitemap.xml \
  | grep -oE '<loc>[^<]+' | sed 's|<loc>||' \
  | xargs -I{} curl -s -o /dev/null -w "%{http_code} {}\n" {}

# 3. Each page has exactly one <h1>
for url in $(curl -s https://azuremastery.app/sitemap.xml | grep -oE '<loc>[^<]+' | sed 's|<loc>||'); do
  count=$(curl -s "$url" | grep -ciE '<h1[ >]')
  echo "$count $url"
done
# Expect: 1 for every URL.

# 4. JSON-LD parses cleanly on each new cert page
curl -s https://azuremastery.app/exams/az-104/ \
  | python3 -c 'import sys, re, json; m=re.findall(r"<script type=\"application/ld\+json\">(.+?)</script>", sys.stdin.read(), re.S); [json.loads(s) for s in m]; print("OK")'

# 5. No accidental noindex
curl -s https://azuremastery.app/exams/az-104/ | grep -i 'name="robots"'
# Expect: 'index, follow' (or no robots meta, which defaults to index).

# 6. Page weight stays sane
curl -sI https://azuremastery.app/exams/az-104/ | grep -i content-length
# Warn if > 100KB for a cert page.
```

After each cert page goes live, paste its URL into [Google Rich Results Test](https://search.google.com/test/rich-results) and confirm `FAQPage` validates with no errors.

---

## 7. Suggested first action

1. Read this entire document.
2. Read `apps/AzureMastery/index.html` (it's large — use offset/limit; the inline `<style>` is around lines 109–1290).
3. Ask Chris the four questions in §5.
4. Once you have answers (or while waiting), create `exams/styles.css` per §2.2.
5. Create `exams/_template.html` per §2.3.
6. Build `/exams/az-900/index.html` first (lowest stakes).
7. **Show Chris the diff. Do not commit.** Wait for explicit approval.

---

## 8. Out of scope for Phase 2

- Tier 2/3/4 cert pages (the remaining 17 of 22). Separate planning session.
- Pillar / blog content (Phase 3 in the original plan). Defer until Phase 2 has indexed.
- Migrating the homepage to root (Option A). Separate decision.
- Removing or replacing Google Analytics. Surface the conflict to Chris; do **not** silently change.
- The marketing-folder `.webloc` cleanup (lives outside this repo). Chris runs that manually.

---

*Last updated: 2026-05-08, after Phase 1 merged via PR #2.*
