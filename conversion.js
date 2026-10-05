/* Progressive enhancements for browsing; no query or answer analytics. */
(function () {
  'use strict';
  document.querySelectorAll('[data-exam-finder]').forEach(function (finder) {
    var buttons = Array.from(finder.querySelectorAll('[data-exam-filter]'));
    var cards = Array.from(finder.querySelectorAll('[data-exam-category]'));
    var status = finder.querySelector('[data-exam-count]');
    var sections = Array.from(finder.querySelectorAll('[data-exam-section]'));
    finder.querySelector('[data-exam-filters]').hidden = false;
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        var category = button.dataset.examFilter;
        buttons.forEach(function (item) { item.setAttribute('aria-pressed', String(item === button)); });
        cards.forEach(function (card) { card.hidden = category !== 'all' && card.dataset.examCategory !== category; });
        sections.forEach(function (section) {
          section.hidden = !Array.from(section.querySelectorAll('[data-exam-category]')).some(function (card) { return !card.hidden; });
        });
        var count = cards.filter(function (card) { return !card.hidden; }).length;
        status.textContent = count + ' current exams' + (category === 'all' ? '' : ' in ' + button.textContent.trim()) + '.';
      });
    });
  });
})();
/* Show UK prices to visitors in the UK; everyone else sees the US reference price.
   Uses the browser's own time zone and language only; nothing is sent anywhere. */
(function () {
  'use strict';
  var prices = document.querySelectorAll('[data-price-usd]');
  if (!prices.length) return;
  var uk = false;
  try {
    uk = Intl.DateTimeFormat().resolvedOptions().timeZone === 'Europe/London' ||
      /-GB$/i.test(navigator.language || '');
  } catch (e) { return; }
  if (!uk) return;
  prices.forEach(function (node) { node.textContent = node.dataset.priceGbp; });
  document.querySelectorAll('[data-price-region-gbp]').forEach(function (node) { node.textContent = node.dataset.priceRegionGbp; });
})();
