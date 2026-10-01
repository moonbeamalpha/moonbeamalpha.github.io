/* A small, local practice preview. Answers and explanations never leave the browser. */
(function () {
  'use strict';
  // Each exam keeps its position and answers locally when the visitor switches.
  var flows = new Map();
  document.querySelectorAll('[data-practice-flow]').forEach(function (flow) {
    var cards = Array.from(flow.querySelectorAll('[data-practice-card]'));
    var controls = flow.querySelector('.practice-exams');
    var status = flow.querySelector('[data-practice-progress]');
    var restart = flow.querySelector('[data-practice-restart]');
    if (!cards.length || !controls || !status || !restart) return;
    var selection = 'AZ-900', positions = {}, answered = new Set();
    function selectedCards() { return cards.filter(function (card) { return card.dataset.practiceExam === selection; }); }
    function update(focus) {
      var sample = selectedCards(), position = positions[selection] || 0;
      var active = sample[position];
      cards.forEach(function (card) { card.hidden = card !== active; });
      controls.querySelectorAll('button').forEach(function (button) { button.setAttribute('aria-pressed', String(button.dataset.practiceSelect === selection)); });
      var completed = sample.filter(function (card) { return answered.has(card); }).length;
      status.textContent = selection + ' · Question ' + (position + 1) + ' of ' + sample.length + ' · ' + completed + ' answered' + (completed === sample.length ? ' · Sample complete' : '');
      var download = flow.querySelector('[data-practice-download]');
      if (download) download.href = 'https://apps.apple.com/app/id6760594569?pt=128558698&mt=8&ct=site-preview-' + selection.toLowerCase();
      var examLink = flow.querySelector('[data-practice-exam-link]');
      if (examLink) { examLink.href = '/exams/' + selection.toLowerCase() + '/'; examLink.textContent = 'Explore ' + selection + ' →'; }
      if (focus) active.querySelector('.qt__viz-q').focus();
    }
    controls.querySelectorAll('button').forEach(function (button) {
      button.addEventListener('click', function () { selection = button.dataset.practiceSelect; update(false); });
    });
    restart.addEventListener('click', function () {
      selectedCards().forEach(function (card) { answered.delete(card); card.querySelector('[data-quiz]').dispatchEvent(new Event('practice:reset')); });
      positions[selection] = 0; update(true);
    });
    controls.hidden = status.hidden = restart.hidden = false;
    cards.forEach(function (card) {
      flows.set(card.querySelector('[data-quiz]'), {
        grade: function () { answered.add(card); update(false); },
        reset: function () { answered.delete(card); update(false); },
        next: function () { positions[selection] = (positions[selection] || 0) + 1; update(true); },
        isLast: Number(card.dataset.practicePosition) === cards.filter(function (other) { return other.dataset.practiceExam === card.dataset.practiceExam; }).length
      });
    });
    flow.querySelector('[data-practice-cards]').classList.add('practice-enhanced');
    update(false);
  });
  document.querySelectorAll('.qt__viz[data-quiz]').forEach(function (quiz, quizIndex) {
    var options = Array.from(quiz.querySelectorAll('.qt__viz-options li'));
    if (!options.every(function (option) { return option.querySelector('.qt__option-text') && option.querySelector('.qt__rationale'); })) return;
    var correct = options.filter(function (option) { return option.classList.contains('is-selected'); });
    if (!correct.length) return;
    var prompt = quiz.querySelector('.qt__viz-q');
    prompt.id = 'practice-question-' + quizIndex;
    prompt.tabIndex = -1;
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
      link.className = 'qt__quiz-link btn-primary'; link.rel = 'noopener noreferrer';
      var code = quiz.dataset.examCode.toLowerCase();
      link.href = 'https://apps.apple.com/app/id6760594569?pt=128558698&mt=8&ct=' +
        (location.pathname === '/' ? 'site-preview-' : 'exam-') + code + (location.pathname === '/' ? '' : '-quiz');
      link.textContent = 'Continue practising free in the app';
      var reset = document.createElement('button');
      reset.type = 'button'; reset.className = 'qt__reset'; reset.textContent = 'Retry question';
      reset.addEventListener('click', function () { resetQuestion(); options[0].querySelector('button').focus(); });
      function resetQuestion() {
        done = false; picked.clear(); note.textContent = ''; feedback.replaceChildren(note); feedback.classList.remove('has-answer'); hint.hidden = false;
        quiz.setAttribute('aria-describedby', hint.id);
        check.hidden = correct.length === 1; check.disabled = true;
        options.forEach(function (option) {
          option.classList.remove('is-picked', 'is-correct', 'is-wrong');
          var button = option.querySelector('button'); button.removeAttribute('aria-disabled'); button.setAttribute('aria-pressed', 'false');
          button.querySelector('.qt__option-state').hidden = true;
        });
        var flow = flows.get(quiz); if (flow) flow.reset();
      }
      // Replace the reset handler on each grade, rather than accumulating listeners.
      quiz.onpracticereset = resetQuestion;
      var flow = flows.get(quiz);
      if (flow && !flow.isLast) {
        var next = document.createElement('button'); next.type = 'button'; next.className = 'qt__next'; next.textContent = 'Next question';
        next.addEventListener('click', flow.next); actions.append(next);
      }
      if (flow && flow.isLast) {
        var finish = document.createElement('p'); finish.className = 'qt__sample-complete';
        finish.textContent = 'That’s the end of this sample. Keep going with 50+ free questions per exam in the app.';
        feedback.appendChild(finish);
      }
      actions.append(link, reset); feedback.appendChild(actions);
      if (flow) flow.grade();
      if (wasChecking) options.find(function (option) { return picked.has(option); }).querySelector('button').focus({ preventScroll: true });
    }
    check.addEventListener('click', grade);
    quiz.addEventListener('practice:reset', function () { if (quiz.onpracticereset) quiz.onpracticereset(); });
  });
})();
