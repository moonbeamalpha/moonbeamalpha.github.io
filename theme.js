/* Azure Mastery theme toggle. Dark is the default; light is opt-in and
   persisted under 'am-theme'. The inline head snippet applies a stored
   'light' choice before first paint; this script wires up the buttons
   and keeps the color-scheme / theme-color metas in sync (the iOS Smart
   Banner reads them, so they must always match the rendered theme). */
(function () {
  var KEY = 'am-theme';
  var root = document.documentElement;
  var transitioning = false;
  var backgroundObserver = null;

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function persist(value) {
    try { localStorage.setItem(KEY, value); } catch (e) { /* private mode: theme still applies for this pageview */ }
  }

  function applyScreenshotSources(light) {
    var images = document.querySelectorAll('[data-theme-src-light]');
    for (var i = 0; i < images.length; i++) {
      var image = images[i];
      var darkSource = image.getAttribute('data-theme-src-dark');
      if (!darkSource) {
        darkSource = image.getAttribute('src');
        image.setAttribute('data-theme-src-dark', darkSource);
      }
      var desiredSource = light ? image.getAttribute('data-theme-src-light') : darkSource;
      if (desiredSource && image.getAttribute('src') !== desiredSource) {
        image.setAttribute('src', desiredSource);
      }
    }

    var loadedBackgrounds = document.querySelectorAll('[data-theme-bg-loaded="true"]');
    for (var j = 0; j < loadedBackgrounds.length; j++) {
      applyThemedBackground(loadedBackgrounds[j], light);
    }
  }

  function applyThemedBackground(element, light) {
    var source = light ? element.getAttribute('data-theme-bg-light') : element.getAttribute('data-theme-bg-dark');
    if (!source) source = element.getAttribute('data-theme-bg-dark');
    if (!source) return;
    element.style.backgroundImage = 'url("' + source.replace(/"/g, '\\"') + '")';
    element.setAttribute('data-theme-bg-loaded', 'true');
  }

  function initLazyBackgrounds() {
    var backgrounds = document.querySelectorAll('[data-theme-bg-dark]');
    if (!backgrounds.length) return;

    var light = root.getAttribute('data-theme') === 'light';
    if (!('IntersectionObserver' in window)) {
      for (var i = 0; i < backgrounds.length; i++) applyThemedBackground(backgrounds[i], light);
      return;
    }

    backgroundObserver = new IntersectionObserver(function(entries) {
      for (var i = 0; i < entries.length; i++) {
        if (!entries[i].isIntersecting) continue;
        applyThemedBackground(entries[i].target, root.getAttribute('data-theme') === 'light');
        backgroundObserver.unobserve(entries[i].target);
      }
    }, { rootMargin: '700px 0px' });

    for (var j = 0; j < backgrounds.length; j++) backgroundObserver.observe(backgrounds[j]);
  }

  function apply(theme) {
    var light = theme === 'light';
    if (light) { root.setAttribute('data-theme', 'light'); } else { root.removeAttribute('data-theme'); }
    applyScreenshotSources(light);
    var scheme = document.querySelector('meta[name="color-scheme"]');
    if (scheme) { scheme.content = light ? 'light' : 'dark'; }
    var tint = document.querySelector('meta[name="theme-color"]');
    if (tint) { tint.content = light ? '#F5F7FA' : '#050810'; }
    var buttons = document.querySelectorAll('.theme-toggle');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', String(light));
      buttons[i].setAttribute('aria-label', light ? 'Switch to dark theme' : 'Switch to light theme');
    }
  }

  function commit(theme) {
    apply(theme);
    persist(theme);
  }

  function fallbackFade(theme) {
    transitioning = true;
    root.classList.add('theme-fade-ready');
    void root.offsetWidth;
    root.classList.add('theme-fade-out');
    window.setTimeout(function () {
      commit(theme);
      root.classList.remove('theme-fade-out');
      root.classList.add('theme-fade-in');
      window.setTimeout(function () {
        root.classList.remove('theme-fade-ready', 'theme-fade-in');
        transitioning = false;
      }, 170);
    }, 150);
  }

  function onToggle() {
    if (transitioning) { return; }
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      commit(next);
      return;
    }

    if (document.startViewTransition) {
      transitioning = true;
      try {
        var transition = document.startViewTransition(function () { commit(next); });
        transition.finished.then(function () { transitioning = false; }, function () { transitioning = false; });
      } catch (e) {
        transitioning = false;
        fallbackFade(next);
      }
      return;
    }

    fallbackFade(next);
  }

  function init() {
    var buttons = document.querySelectorAll('.theme-toggle');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].hidden = false;
      buttons[i].addEventListener('click', onToggle);
    }
    apply(stored() === 'light' ? 'light' : 'dark');
    initLazyBackgrounds();

    if ('serviceWorker' in navigator && window.isSecureContext) {
      window.addEventListener('load', function () {
        navigator.serviceWorker.register('/sw.js').catch(function () { /* caching is optional */ });
      }, { once: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
