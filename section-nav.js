/* Compact mobile contents and a download action that appears only when needed. */
(function () {
  'use strict';
  var main = document.querySelector('main');
  if (!main) return;
  var sections = Array.from(main.querySelectorAll(':scope > section[id]'));
  if (!sections.length) sections = Array.from(main.querySelectorAll('section[id]'));
  if (!sections.length) return;
  var labels = { hero: 'Overview', 'am-cert-hero': 'Overview', 'what-is': 'Overview',
    'question-types': 'Try a question', objectives: 'Exam skills', 'how-helps': 'Study tools',
    'study-plan': 'Study plan', 'cert-paths': 'Certification paths', related: 'Related exams',
    guides: 'Study guides', faqs: 'Questions', 'exam-roadmap': 'Exams', 'try-a-question': 'Try a question',
    pricing: 'Free & Pro', features: 'Study tools', 'video-overview': 'Aura video',
    screenshots: 'App screens', devices: 'Your devices', faq: 'Questions', download: 'Download' };
  function labelFor(section) {
    return section.dataset.navLabel || labels[section.id] ||
      ((section.querySelector('h1,h2') || {}).textContent || section.id).replace(/\s+/g, ' ').trim().split(' ').slice(0, 4).join(' ');
  }
  var storeLink = main.querySelector('a[href*="apps.apple.com"]');
  var nav = document.createElement('nav'); nav.className = 'section-nav section-nav--cta-suppressed';
  nav.setAttribute('aria-label', 'Page sections');
  nav.innerHTML = '<button class="section-nav__menu-button" type="button" aria-expanded="false" aria-controls="section-nav-panel">Contents</button>' +
    '<span class="section-nav__label"></span>' +
    (storeLink ? '<a class="section-nav__cta" rel="noopener noreferrer">Download</a>' : '') +
    '<div class="section-nav__panel" id="section-nav-panel" hidden></div>';
  var menu = nav.querySelector('button'), panel = nav.querySelector('.section-nav__panel'), cta = nav.querySelector('.section-nav__cta');
  if (cta) {
    var url = new URL(storeLink.href); var ct = url.searchParams.get('ct') || 'site';
    url.searchParams.set('ct', ct.replace(/-(?:hero|nav|body)$/, '').slice(0, 23) + '-sticky'); cta.href = url.toString();
  }
  sections.forEach(function (section) {
    var link = document.createElement('a'); link.href = '#' + section.id; link.textContent = labelFor(section); panel.appendChild(link);
  });
  document.body.appendChild(nav); document.body.classList.add('section-nav-ready');
  function close() { panel.hidden = true; menu.setAttribute('aria-expanded', 'false'); }
  menu.addEventListener('click', function () { var open = panel.hidden; panel.hidden = !open; menu.setAttribute('aria-expanded', String(open)); });
  panel.addEventListener('click', function (event) {
    var link = event.target.closest('a'); if (!link) return; close();
    var target = document.getElementById(link.hash.slice(1));
    if (target) { target.setAttribute('tabindex', '-1'); target.focus({ preventScroll: true }); }
  });
  document.addEventListener('click', function (event) { if (!nav.contains(event.target)) close(); });
  document.addEventListener('keydown', function (event) { if (event.key === 'Escape' && !panel.hidden) { close(); menu.focus(); } });
  function update() {
    var current = 0;
    sections.forEach(function (section, index) { if (section.getBoundingClientRect().top <= 150) current = index; });
    nav.querySelector('.section-nav__label').textContent = labelFor(sections[current]);
    Array.from(panel.children).forEach(function (link, index) {
      if (index === current) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
    });
    if (!cta) return;
    var pastHero = storeLink.getBoundingClientRect().bottom <= 80;
    var visible = Array.from(main.querySelectorAll('a[href*="apps.apple.com"]')).some(function (link) {
      var rect = link.getBoundingClientRect();
      return rect.width > 0 && rect.bottom > 80 && rect.top < window.innerHeight - 80;
    });
    nav.classList.toggle('section-nav--cta-suppressed', !pastHero || visible);
  }
  var scheduled = false;
  window.addEventListener('scroll', function () {
    if (scheduled) return; scheduled = true;
    requestAnimationFrame(function () { scheduled = false; update(); });
  }, { passive: true });
  window.addEventListener('resize', update); update();
})();
