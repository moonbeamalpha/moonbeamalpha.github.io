(function () {
  var main = document.querySelector('main');
  if (!main) return;

  var sections = Array.prototype.slice.call(main.querySelectorAll(':scope > section[id]'));
  if (!sections.length) sections = Array.prototype.slice.call(main.querySelectorAll('section[id]'));
  if (!sections.length) return;

  function labelFor(section) {
    return section.getAttribute('data-nav-label') ||
      ((section.querySelector('h1, h2') || {}).textContent || section.id)
        .replace(/\s+/g, ' ').trim();
  }

  var storeLink = document.querySelector('a[href*="apps.apple.com"]');
  var nav = document.createElement('nav');
  nav.className = 'section-nav';
  nav.setAttribute('aria-label', 'Page sections');
  nav.innerHTML =
    '<button class="section-nav__menu-button" type="button" aria-expanded="false" aria-controls="section-nav-panel" aria-label="Show all page sections"><span></span></button>' +
    '<div class="section-nav__track">' +
      '<button class="section-nav__direction section-nav__previous" type="button" aria-label="Previous section">‹</button>' +
      '<div class="section-nav__status" aria-live="polite"><span class="section-nav__label"></span><span class="section-nav__progress"></span></div>' +
      '<button class="section-nav__direction section-nav__next" type="button" aria-label="Next section">›</button>' +
    '</div>' +
    (storeLink ? '<a class="section-nav__cta" rel="noopener noreferrer">Download</a>' : '') +
    '<div class="section-nav__panel" id="section-nav-panel" hidden></div>';

  var menuButton = nav.querySelector('.section-nav__menu-button');
  var previous = nav.querySelector('.section-nav__previous');
  var next = nav.querySelector('.section-nav__next');
  var currentLabel = nav.querySelector('.section-nav__label');
  var progress = nav.querySelector('.section-nav__progress');
  var panel = nav.querySelector('.section-nav__panel');
  var cta = nav.querySelector('.section-nav__cta');
  if (cta) cta.href = storeLink.href;

  sections.forEach(function (section) {
    var link = document.createElement('a');
    link.href = '#' + section.id;
    link.textContent = labelFor(section);
    panel.appendChild(link);
  });

  document.body.appendChild(nav);
  document.body.classList.add('section-nav-ready');

  var index = 0;
  function setCurrent(nextIndex) {
    index = Math.max(0, Math.min(sections.length - 1, nextIndex));
    currentLabel.textContent = labelFor(sections[index]);
    progress.textContent = (index + 1) + ' of ' + sections.length;
    previous.disabled = index === 0;
    next.disabled = index === sections.length - 1;
    Array.prototype.forEach.call(panel.children, function (link, linkIndex) {
      if (linkIndex === index) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  }

  function go(offset) {
    var target = sections[index + offset];
    if (!target) return;
    target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    setCurrent(index + offset);
  }

  previous.addEventListener('click', function () { go(-1); });
  next.addEventListener('click', function () { go(1); });
  menuButton.addEventListener('click', function () {
    var open = panel.hidden;
    panel.hidden = !open;
    menuButton.setAttribute('aria-expanded', String(open));
  });
  panel.addEventListener('click', function (event) {
    var link = event.target.closest('a');
    if (!link) return;
    panel.hidden = true;
    menuButton.setAttribute('aria-expanded', 'false');
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !panel.hidden) {
      panel.hidden = true;
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.focus();
    }
  });

  if ('IntersectionObserver' in window) {
    var visible = new Map();
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) visible.set(entry.target, entry.boundingClientRect.top);
        else visible.delete(entry.target);
      });
      var best = null;
      visible.forEach(function (top, section) {
        if (!best || Math.abs(top) < Math.abs(best.top)) best = { section: section, top: top };
      });
      if (best) setCurrent(sections.indexOf(best.section));
    }, { rootMargin: '-28% 0px -58% 0px', threshold: 0 });
    sections.forEach(function (section) { observer.observe(section); });

    var conversionTargets = document.querySelectorAll('.am-cert-hero__cta, .exam-inline-cta, .guide-inline-cta, .cta-final, .section-final-cta');
    var conversionVisible = new Set();
    var conversionObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) conversionVisible.add(entry.target);
        else conversionVisible.delete(entry.target);
      });
      nav.classList.toggle('section-nav--cta-suppressed', conversionVisible.size > 0);
    }, { threshold: .15 });
    Array.prototype.forEach.call(conversionTargets, function (target) { conversionObserver.observe(target); });
  }

  setCurrent(0);
})();
