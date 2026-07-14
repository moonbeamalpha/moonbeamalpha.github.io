/* Azure Mastery theme toggle. Dark is the default; light is opt-in and
   persisted under 'am-theme'. The inline head snippet applies a stored
   'light' choice before first paint; this script wires up the buttons
   and keeps the color-scheme / theme-color metas in sync (the iOS Smart
   Banner reads them, so they must always match the rendered theme). */
(function () {
  var KEY = 'am-theme';
  var root = document.documentElement;

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
      image.setAttribute('src', light ? image.getAttribute('data-theme-src-light') : darkSource);
    }
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

  function onToggle() {
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.classList.add('theme-lock');
    void root.offsetWidth;
    apply(next);
    persist(next);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { root.classList.remove('theme-lock'); });
    });
  }

  function init() {
    var buttons = document.querySelectorAll('.theme-toggle');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].hidden = false;
      buttons[i].addEventListener('click', onToggle);
    }
    apply(stored() === 'light' ? 'light' : 'dark');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
