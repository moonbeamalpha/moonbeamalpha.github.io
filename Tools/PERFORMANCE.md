# Homepage performance maintenance

Edit `home.css` and `theme-light.css`, then run `bash Tools/build-home-css.sh`.
The homepage serves their generated, minified bundle, `home.min.css`. CI checks
for drift; do not edit the bundle directly. The pinned clean-css build requires
Node/npm and registry access on its first run.

Run `node Tools/check-marketing-performance.mjs` for dependency-free regression
checks, alongside the existing SEO and generated-count checks.

The hero is visible without JavaScript. Below-fold decorative screenshots use
`data-theme-bg-dark` / `data-theme-bg-light`; `theme.js` loads them near the
viewport. Add a dark image rule to the homepage's `noscript` fallback whenever
adding a lazy screenshot. Both theme variants must exist on disk.

Use one Google Analytics loader per page. Pages with direct GA must not also
load the GTM container. GTM-only legacy pages keep their existing loader.

`sw.js` caches only same-origin images/fonts on demand, serving a cached copy
while refreshing it in the background. It does not precache, intercept HTML,
cache analytics, or override CSS/JavaScript requests. This improves repeat visits
without coupling current HTML to old application code. It is not offline-site
support. Cache storage failures do not block a network response.

GitHub Pages still controls HTTP cache headers (currently ten minutes). The
service worker does not change those headers. A CDN migration or longer HTTP
TTL requires a separate deployment decision and versioned asset URLs. If image
freshness is critical, change its filename; otherwise a repeat visitor can see
the previous image during background refresh. Bump the worker cache version to
discard all previously stored media.
