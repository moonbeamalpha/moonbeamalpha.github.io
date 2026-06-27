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
  
