/* A small, local practice preview. Answers and explanations never leave the browser. */
(function () {
  'use strict';
  document.querySelectorAll('.qt__viz[data-quiz]').forEach(function (quiz) {
    var options = Array.from(quiz.querySelectorAll('.qt__viz-options li'));
    if (!options.every(function (option) { return option.querySelector('.qt__option-text') && option.querySelector('.qt__rationale'); })) return;
    var correct = options.filter(function (option) { return option.classList.contains('is-selected'); });
    if (!correct.length) return;
    var picked = new Set(), done = false;
    var hint = document.createElement('p');
    hint.className = 'qt__quiz-hint';
    hint.textContent = correct.length > 1 ? 'Choose ' + correct.length + ' answers, then check.' : 'Choose an answer to see the explanation.';
    quiz.appendChild(hint);
    var check = document.createElement('button');
    check.type = 'button'; check.className = 'qt__check'; check.textContent = 'Check answers';
    check.hidden = correct.length === 1; check.disabled = true;
    quiz.appendChild(check);
    options.forEach(function (option) {
      option.classList.remove('is-selected');
      var button = document.createElement('button');
      button.type = 'button'; button.className = 'qt__option-button';
      button.textContent = option.querySelector('.qt__option-text').textContent;
      button.setAttribute('aria-pressed', 'false');
      option.querySelector('.qt__option-text').replaceWith(button);
      button.addEventListener('click', function () {
        if (done) return;
        if (picked.has(option)) picked.delete(option); else picked.add(option);
        option.classList.toggle('is-picked', picked.has(option));
        button.setAttribute('aria-pressed', String(picked.has(option)));
        check.disabled = picked.size !== correct.length;
        if (correct.length === 1) grade();
      });
    });
    var feedback = document.createElement('div');
    feedback.className = 'qt__feedback'; feedback.setAttribute('role', 'status');
    feedback.setAttribute('aria-live', 'polite'); quiz.appendChild(feedback);
    function grade() {
      done = true;
      var right = picked.size === correct.length && correct.every(function (option) { return picked.has(option); });
      hint.hidden = true; check.hidden = true;
      var note = document.createElement('p');
      note.className = 'qt__quiz-note';
      note.textContent = right ? 'Correct. Here is the reasoning for each option.' : 'Not quite. Compare your choice with the correct answer and its rationale.';
      feedback.appendChild(note);
      options.forEach(function (option) {
        var isCorrect = correct.includes(option);
        option.classList.toggle('is-correct', isCorrect);
        option.classList.toggle('is-wrong', picked.has(option) && !isCorrect);
        var button = option.querySelector('button'); button.disabled = true;
        var rationale = option.querySelector('.qt__rationale');
        rationale.hidden = false;
        var label = document.createElement('strong');
        label.textContent = (isCorrect ? 'Correct answer. ' : 'Other option. ') + (picked.has(option) ? 'Your choice. ' : '');
        rationale.prepend(label);
      });
      var link = document.createElement('a');
      link.className = 'qt__quiz-link'; link.rel = 'noopener noreferrer';
      var code = quiz.dataset.examCode.toLowerCase();
      link.href = 'https://apps.apple.com/app/id6760594569?pt=128558698&mt=8&ct=' +
        (location.pathname === '/' ? 'site-preview-' : 'exam-') + code + (location.pathname === '/' ? '' : '-quiz');
      link.textContent = 'Continue ' + quiz.dataset.examCode + ' practice in the app →';
      feedback.appendChild(link);
      var reset = document.createElement('button');
      reset.type = 'button'; reset.className = 'qt__reset'; reset.textContent = 'Try this question again';
      reset.addEventListener('click', function () {
        done = false; picked.clear(); feedback.replaceChildren(); hint.hidden = false;
        check.hidden = correct.length === 1; check.disabled = true;
        options.forEach(function (option) {
          option.classList.remove('is-picked', 'is-correct', 'is-wrong');
          var button = option.querySelector('button'); button.disabled = false; button.setAttribute('aria-pressed', 'false');
          var rationale = option.querySelector('.qt__rationale'); rationale.hidden = true;
          rationale.querySelector('strong').remove();
        });
        options[0].querySelector('button').focus();
      });
      feedback.appendChild(reset);
    }
    check.addEventListener('click', grade);
  });
})();
