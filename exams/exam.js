/* Shared exam-page behaviour — linked by every /exams/<code>/ page via <script src defer>.
   Both blocks are guarded IIFEs and no-op when their elements are absent. */

// TOC scroll-spy (highlights the active 'On this page' link)
(function () {
  var links = document.querySelectorAll('.page-toc__link');
  if (!links.length || !('IntersectionObserver' in window)) return;
  var map = new Map();
  links.forEach(function (a) {
    var id = a.getAttribute('href').slice(1);
    var sec = document.getElementById(id);
    if (sec) map.set(sec, a);
  });
  var active = new Set();
  function setActive(link) {
    links.forEach(function (a) { a.removeAttribute('aria-current'); });
    if (link) link.setAttribute('aria-current', 'true');
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) active.add(e.target); else active.delete(e.target);
    });
    var topSec = null, topY = Infinity;
    active.forEach(function (sec) {
      var y = sec.getBoundingClientRect().top;
      if (y < topY) { topY = y; topSec = sec; }
    });
    setActive(topSec ? map.get(topSec) : null);
  }, { rootMargin: '-25% 0px -65% 0px', threshold: 0 });
  map.forEach(function (_, sec) { io.observe(sec); });
})();
  

// App Store link attribution — stamps the exam's campaign token onto every
// store link so a download can be traced back to the page that produced it.
//
// Why this lives in JS rather than in each page's markup: there are three store
// links per exam page across 32 pages, and every future page cloned from the
// template inherits the behaviour for free. The token is derived from the URL,
// so a new exam page needs no attribution work at all.
//
// The token format keeps the hyphen (`exam-ab-620`) because both the analytics
// warehouse and App Store Connect parse the exam code back out of it.
//
// GA4 enhanced measurement already records outbound clicks together with the
// link URL, so rewriting the href is sufficient — no explicit event is emitted
// here, which would double-count.
(function () {
  // Apple credits a campaign in App Analytics only when a provider token
  // accompanies the campaign token. Set it here — one edit covers all 32 exam
  // pages and every page cloned from the template afterwards.
  //
  // Find the value in App Store Connect → App Analytics → Acquisition →
  // Campaigns → Create Campaign; the generated link contains `pt=<token>`.
  // It is not a secret (it ships in every outbound link) but it must be exact:
  // a wrong token is accepted silently and simply never attributes.
  //
  // Leaving it empty is safe. Campaign tokens are still stamped, so Google
  // Analytics attribution works fully; only Apple's own campaign report stays
  // blank until this is filled in.
  var APPLE_PROVIDER_TOKEN = '128558698';

  var match = window.location.pathname.match(/\/exams\/([a-z]{2,3}-\d{3})\//i);
  if (!match) return;
  var campaign = 'exam-' + match[1].toLowerCase();

  // A per-page override wins, so a single page can be pointed at a different
  // provider without touching this file.
  var providerToken = document.documentElement.getAttribute('data-apple-provider-token')
    || APPLE_PROVIDER_TOKEN;

  var links = document.querySelectorAll('a[href*="apps.apple.com"]');
  Array.prototype.forEach.call(links, function (link) {
    var href = link.getAttribute('href');
    if (!href) return;
    try {
      var url = new URL(href, window.location.origin);
      if (url.hostname !== 'apps.apple.com') return;
      // Never overwrite a token already set deliberately in the markup.
      if (!url.searchParams.get('ct')) url.searchParams.set('ct', campaign);
      if (providerToken && !url.searchParams.get('pt')) url.searchParams.set('pt', providerToken);
      if (!url.searchParams.get('mt')) url.searchParams.set('mt', '8');
      link.setAttribute('href', url.toString());
    } catch (error) {
      // A malformed href is left exactly as authored; attribution is never
      // worth breaking a download link over.
    }
  });
})();


// Microsoft-retirement banner (revealed only when retired or <=30 days out)
/* Show the retirement banner only when the exam is retired or retires within 30 days. */
(function () {
  var b = document.querySelector('.am-retire-banner[data-retire-date]');
  if (!b) return;
  var d = new Date(b.getAttribute('data-retire-date') + 'T00:00:00');
  if (isNaN(d.getTime())) return;
  var days = Math.ceil((d - new Date()) / 86400000);
  if (days > 30) return; // outside the window — leave hidden
  var cert = b.getAttribute('data-cert');
  var when = d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  var t = b.querySelector('.am-retire-banner__text');
  t.innerHTML = days <= 0
    ? '<strong>' + cert + ' was retired by Microsoft on ' + when + '.</strong> Microsoft no longer offers this exam.'
    : '<strong>Microsoft retires ' + cert + ' on ' + when + '.</strong> It won\u2019t be available to book after that date.';
  b.hidden = false;
})();
  
