/* Progressive enhancements for browsing; no query or answer analytics. */
(function () {
  'use strict';
  document.querySelectorAll('[data-exam-finder]').forEach(function (finder) {
    var buttons = Array.from(finder.querySelectorAll('[data-exam-filter]'));
    var cards = Array.from(finder.querySelectorAll('[data-exam-category]'));
    var more = finder.querySelector('.exam-finder__more');
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
        if (more) more.open = category !== 'all';
        var count = cards.filter(function (card) { return !card.hidden; }).length;
        status.textContent = count + ' current exams' + (category === 'all' ? '' : ' in ' + button.textContent.trim()) + '.';
      });
    });
  });
})();
