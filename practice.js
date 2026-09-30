/* A small, local practice preview. Answers and explanations never leave the browser. */
(function () {
  'use strict';
  document.querySelectorAll('.qt__viz[data-quiz]').forEach(function (quiz, quizIndex) {
    var options = Array.from(quiz.querySelectorAll('.qt__viz-options li'));
    if (!options.every(function (option) { return option.querySelector('.qt__option-text') && option.querySelector('.qt__rationale'); })) return;
    var correct = options.filter(function (option) { return option.classList.contains('is-selected'); });
    if (!correct.length) return;
    var prompt = quiz.querySelector('.qt__viz-q');
    prompt.id = 'practice-question-' + quizIndex;
    quiz.setAttribute('role', 'group'); quiz.setAttribute('aria-labelledby', prompt.id);
    var picked = new Set(), done = false;
    var hint = document.createElement('p');
    hint.className = 'qt__quiz-hint';
    hint.id = 'practice-hint-' + quizIndex;
    quiz.setAttribute('aria-describedby', hint.id);
    hint.textContent = correct.length > 1 ? 'Choose ' + correct.length + ' answers, then check.' : 'Choose an answer to reveal the reasoning.';
    quiz.appendChild(hint);
    var check = document.createElement('button');
    check.type = 'button'; check.className = 'qt__check'; check.textContent = 'Check answers';
    check.hidden = correct.length === 1; check.disabled = true;
    quiz.appendChild(check);
    options.forEach(function (option, index) {
      option.classList.remove('is-selected');
      var button = document.createElement('button');
      button.type = 'button'; button.className = 'qt__option-button';
      var letter = document.createElement('span');
      letter.className = 'qt__option-letter'; letter.setAttribute('aria-hidden', 'true');
      letter.textContent = String.fromCharCode(65 + index);
      var text = document.createElement('span'); text.className = 'qt__option-label';
      text.textContent = option.querySelector('.qt__option-text').textContent;
      var state = document.createElement('span'); state.className = 'qt__option-state'; state.hidden = true;
      button.append(letter, text, state);
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
    var feedback = document.createElement('div'); feedback.className = 'qt__feedback';
    var note = document.createElement('p'); note.className = 'qt__quiz-note';
    note.id = 'practice-feedback-' + quizIndex;
    note.setAttribute('role', 'status'); note.setAttribute('aria-live', 'polite');
    feedback.appendChild(note); quiz.appendChild(feedback);
    function grade() {
      done = true;
      var wasChecking = document.activeElement === check;
      var right = picked.size === correct.length && correct.every(function (option) { return picked.has(option); });
      hint.hidden = true; check.hidden = true;
      feedback.classList.add('has-answer');
      note.classList.toggle('is-right', right);
      note.textContent = right ? 'Correct — here’s why.' : 'Not quite — let’s work through it.';
      quiz.setAttribute('aria-describedby', note.id);
      var explanation = document.createElement('div'); explanation.className = 'qt__explanation';
      var others = document.createElement('details'); others.className = 'qt__other-rationales';
      var summary = document.createElement('summary'); summary.textContent = 'Why the other options don’t fit'; others.appendChild(summary);
      options.forEach(function (option) {
        var isCorrect = correct.includes(option), chosen = picked.has(option);
        option.classList.toggle('is-correct', isCorrect);
        option.classList.toggle('is-wrong', chosen && !isCorrect);
        var button = option.querySelector('button'); button.setAttribute('aria-disabled', 'true');
        var state = button.querySelector('.qt__option-state');
        state.hidden = !(isCorrect || chosen);
        state.textContent = isCorrect ? (chosen ? 'Your answer · Correct' : 'Correct answer') : 'Your answer';
        var entry = document.createElement('div');
        var title = document.createElement('h4'); title.textContent = button.querySelector('.qt__option-label').textContent;
        var rationale = document.createElement('p'); rationale.textContent = option.querySelector('.qt__rationale').textContent;
        entry.append(title, rationale);
        (isCorrect ? explanation : others).appendChild(entry);
      });
      feedback.append(explanation, others);
      var actions = document.createElement('div'); actions.className = 'qt__feedback-actions';
      var link = document.createElement('a');
      link.className = 'qt__quiz-link'; link.rel = 'noopener noreferrer';
      var code = quiz.dataset.examCode.toLowerCase();
      link.href = 'https://apps.apple.com/app/id6760594569?pt=128558698&mt=8&ct=' +
        (location.pathname === '/' ? 'site-preview-' : 'exam-') + code + (location.pathname === '/' ? '' : '-quiz');
      link.textContent = 'Continue ' + quiz.dataset.examCode + ' in the app →';
      var reset = document.createElement('button');
      reset.type = 'button'; reset.className = 'qt__reset'; reset.textContent = 'Try again';
      reset.addEventListener('click', function () {
        done = false; picked.clear(); note.textContent = ''; feedback.replaceChildren(note); feedback.classList.remove('has-answer'); hint.hidden = false;
        quiz.setAttribute('aria-describedby', hint.id);
        check.hidden = correct.length === 1; check.disabled = true;
        options.forEach(function (option) {
          option.classList.remove('is-picked', 'is-correct', 'is-wrong');
          var button = option.querySelector('button'); button.removeAttribute('aria-disabled'); button.setAttribute('aria-pressed', 'false');
          button.querySelector('.qt__option-state').hidden = true;
        });
        options[0].querySelector('button').focus();
      });
      actions.append(link, reset); feedback.appendChild(actions);
      if (wasChecking) options.find(function (option) { return picked.has(option); }).querySelector('button').focus({ preventScroll: true });
    }
    check.addEventListener('click', grade);
  });
})();
