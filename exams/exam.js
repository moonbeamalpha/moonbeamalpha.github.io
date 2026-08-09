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

  // Exam pages → ct=exam-<code>; guide pages → ct=guide-<slug>; hub pages →
  // ct=exam-index / guide-index. Guides load this file too, so their store
  // links are attributed in App Store Connect instead of arriving blank.
  var path = window.location.pathname;
  var campaign = null;
  var match = path.match(/\/(exams|guides)\/([a-z0-9][a-z0-9-]*)\/?/i);
  if (match) {
    campaign = (match[1].toLowerCase() === 'exams' ? 'exam-' : 'guide-') + match[2].toLowerCase();
  } else if (/^\/exams\/?$/.test(path)) {
    campaign = 'exam-index';
  } else if (/^\/guides\/?$/.test(path)) {
    campaign = 'guide-index';
  }
  if (!campaign) return;
  campaign = campaign.slice(0, 34);

  // Paid/tagged traffic: fold the acquisition source into the campaign token so
  // Apple's campaign report separates ad-driven installs from organic ones.
  // Tokens stay alphanumeric-with-dashes and under Apple's length ceiling.
  try {
    var qs = new URLSearchParams(window.location.search);
    if (qs.get('fbclid') || /^(fb|ig|an|msg)$/.test(qs.get('utm_source') || '')) {
      campaign += '-ps'; // paid social
    } else if (qs.get('gclid')) {
      campaign += '-pg'; // paid Google
    } else if (qs.get('utm_medium') === 'email') {
      campaign += '-em';
    }
  } catch (e) { /* URLSearchParams unavailable — organic token is fine */ }

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
  

// Tappable sample questions — progressive enhancement over the static
// question-type mockups. Pages mark tappable vizzes with data-quiz="1"
// (multiple-choice and multi-select only); the authored `is-selected`
// classes are the answer key, read then stripped before first paint-frame
// interaction. Without JS the mockups render exactly as before.
(function () {
  var vizzes = document.querySelectorAll('.qt__viz[data-quiz]');
  if (!vizzes.length) return;

  var codeEl = document.querySelector('.am-cert-hero__eyebrow-code');
  var countEl = document.querySelector('.am-cert-hero__stat-count');
  var code = codeEl ? codeEl.textContent.trim() : 'this exam';
  var bank = countEl ? countEl.textContent.trim() : '';
  var storeLink = document.querySelector('a[href*="apps.apple.com"]');
  var answered = 0, right = 0, total = vizzes.length;

  function summarise() {
    var grid = document.querySelector('.question-types');
    if (!grid || document.querySelector('.quiz-summary')) return;
    var p = document.createElement('p');
    p.className = 'quiz-summary';
    var score = '<strong>You got ' + right + ' of ' + total + '.</strong> ';
    var pitch = bank
      ? 'There are ' + bank + ' more ' + code + ' practice questions — each with a full rationale for every option — in the app. '
      : 'Every ' + code + ' question in the app explains every option. ';
    p.innerHTML = score + pitch;
    var a = document.createElement('a');
    a.href = storeLink ? storeLink.href : 'https://apps.apple.com/app/apple-store/id6760594569';
    a.rel = 'noopener noreferrer';
    a.textContent = 'Get the full ' + code + ' bank →';
    p.appendChild(a);
    grid.parentNode.insertBefore(p, grid.nextSibling);
    p.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  Array.prototype.forEach.call(vizzes, function (viz) {
    var options = viz.querySelectorAll('.qt__viz-options li');
    if (!options.length) return;
    var key = [];
    Array.prototype.forEach.call(options, function (li, i) {
      if (li.classList.contains('is-selected')) key.push(i);
      li.classList.remove('is-selected');
      li.setAttribute('tabindex', '0');
      li.setAttribute('role', 'button');
    });
    if (!key.length) return;
    viz.removeAttribute('aria-hidden');
    viz.setAttribute('data-quiz-live', '1');

    var hint = document.createElement('span');
    hint.className = 'qt__quiz-hint';
    hint.textContent = key.length > 1
      ? 'Tap ' + key.length + ' answers to check them'
      : 'Tap an answer to check it';
    viz.appendChild(hint);

    var picked = [], done = false;
    function grade() {
      done = true;
      viz.removeAttribute('data-quiz-live');
      var allRight = picked.length === key.length && picked.every(function (i) { return key.indexOf(i) >= 0; });
      Array.prototype.forEach.call(options, function (li, i) {
        li.removeAttribute('tabindex');
        li.removeAttribute('role');
        if (key.indexOf(i) >= 0) li.classList.add('is-correct');
        else if (picked.indexOf(i) >= 0) li.classList.add('is-wrong');
      });
      if (allRight) right++;
      answered++;
      var note = document.createElement('span');
      note.className = 'qt__quiz-note';
      note.innerHTML = allRight
        ? '<strong>Correct.</strong> The app explains why every other option is wrong, too.'
        : '<strong>Not quite</strong> — the highlighted ' + (key.length > 1 ? 'answers are' : 'answer is') + ' correct. The app’s Answer Coach explains the misconception.';
      hint.replaceWith(note);
      if (answered === total) summarise();
    }
    function pick(i) {
      if (done) return;
      if (picked.indexOf(i) >= 0) {
        picked.splice(picked.indexOf(i), 1);
        options[i].classList.remove('is-picked');
        return;
      }
      picked.push(i);
      options[i].classList.add('is-picked');
      if (picked.length >= key.length) grade();
    }
    Array.prototype.forEach.call(options, function (li, i) {
      li.addEventListener('click', function () { pick(i); });
      li.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(i); }
      });
    });
  });
})();
