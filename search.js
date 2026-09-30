/* Shared browser search. The pure matcher is also exported for Node contract tests. */
(function (root) {
  'use strict';
  var aliases = [
    [/\bpowerbi\b/g, 'power bi'], [/\bm365\b/g, 'microsoft 365'],
    [/\b(?:entra id|azure ad)\b/g, 'identity'], [/\bartificial intelligence\b/g, 'ai'],
    [/\bmlops\b/g, 'machine learning operations'], [/\bnetworking\b/g, 'network'],
  ];
  function normalize(value) {
    var text = String(value).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      .replace(/\b([a-z]{2})[\s\u2010-\u2015-]*(\d{1,3})\b/g, '$1$2');
    aliases.forEach(function (alias) { text = text.replace(alias[0], alias[1]); });
    return text.replace(/[^a-z0-9]+/g, ' ').trim().replace(/\s+/g, ' ');
  }
  function field(text) {
    var normalized = normalize(text);
    return { text: normalized, words: Array.from(new Set(normalized.split(' ').filter(Boolean))) };
  }
  function prepareEntries(entries) {
    return entries.map(function (entry) {
      return { entry: entry, fields: [
        field(entry.title), field((entry.subjects || []).join(' ')),
        field(entry.headings || ''), field(entry.summary), field(entry.text),
      ], codes: (entry.examCodes || []).map(normalize) };
    });
  }
  function oneEdit(a, b) {
    if (Math.abs(a.length - b.length) > 1) return false;
    var i = 0, j = 0, edits = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++edits > 1) return false;
      if (a.length === b.length && a[i] === b[j + 1] && a[i + 1] === b[j]) { i += 2; j += 2; continue; }
      if (a.length >= b.length) i++;
      if (b.length >= a.length) j++;
    }
    return edits + (i < a.length || j < b.length ? 1 : 0) <= 1;
  }
  function tokenMatch(token, words, fuzzy) {
    var numeric = /\d/.test(token);
    if (words.indexOf(token) !== -1) return 1;
    if ((!numeric || /^[a-z]{2}\d{1,2}$/.test(token)) &&
        words.some(function (word) { return word.startsWith(token); })) return 0.75;
    if (fuzzy && !numeric && token.length >= 5 && words.some(function (word) {
      return !/\d/.test(word) && oneEdit(token, word);
    })) return 0.4;
    return 0;
  }
  function searchEntries(prepared, query, kind) {
    var normalized = normalize(query);
    if (normalized.length < 2) return [];
    var tokens = normalized.split(' ').filter(function (word) {
      return !['the', 'and', 'for', 'of', 'in', 'on', 'a', 'with'].includes(word);
    });
    if (!tokens.length) return [];
    var codeQuery = tokens.some(function (token) { return /^[a-z]{2}\d{3}$/.test(token); });
    function rank(fuzzy) {
      return prepared.flatMap(function (item) {
        if (kind && kind !== 'all' && item.entry.kind !== kind) return [];
        var score = 0;
        var matches = tokens.every(function (token) {
          var best = 0;
          item.fields.forEach(function (value, index) {
            best = Math.max(best, tokenMatch(token, value.words, fuzzy) * [120, 95, 55, 30, 8][index]);
          });
          score += best;
          return best > 0;
        });
        if (!matches) return [];
        if (item.fields[0].text.includes(normalized)) score += 180;
        if (tokens.some(function (token) { return item.codes.includes(token); })) {
          score += item.entry.kind === 'exam' ? 10000 : 1000;
        }
        return [{ entry: item.entry, score: score, tokens: tokens }];
      }).sort(function (a, b) {
        if (!codeQuery) {
          var lifecycle = Number(a.entry.status !== 'current') - Number(b.entry.status !== 'current');
          if (lifecycle) return lifecycle;
        }
        return b.score - a.score || a.entry.title.localeCompare(b.entry.title) || a.entry.url.localeCompare(b.entry.url);
      });
    }
    var exact = rank(false);
    return exact.length ? exact : rank(true);
  }
  function excerpt(entry, tokens) {
    var summary = entry.summary || entry.title;
    if (tokens.some(function (token) { return normalize(summary).includes(token); })) return summary.slice(0, 190);
    var source = entry.text || summary;
    var words = source.split(/\s+/);
    var index = words.findIndex(function (word) {
      return tokens.some(function (token) { return normalize(word).includes(token); });
    });
    if (index < 0) return summary.slice(0, 190);
    var start = Math.max(0, index - 7);
    return (start ? '… ' : '') + words.slice(start, start + 28).join(' ').slice(0, 190) + '…';
  }
  var api = { normalize: normalize, prepareEntries: prepareEntries, searchEntries: searchEntries, excerpt: excerpt };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (!root.document) return;

  var document = root.document;
  var script = document.querySelector('script[data-search-index]');
  var dialog = document.getElementById('am-search-dialog');
  if (!script || !dialog || !dialog.showModal) return;
  var indexPromise, prepared, trigger;
  function validPath(value) {
    return typeof value === 'string' && value.startsWith('/') &&
      new URL(value, root.location.origin).origin === root.location.origin;
  }
  function loadIndex() {
    if (!indexPromise) {
      indexPromise = (async function () {
        var controller = new AbortController();
        var timeout = root.setTimeout(function () { controller.abort(); }, 12000);
        try {
          var response = await fetch(script.dataset.searchIndex, { signal: controller.signal });
          if (!response.ok) throw new Error('Index unavailable');
          var data = await response.json();
          if (data.version !== 1 || !Array.isArray(data.entries) || data.entries.some(function (entry) {
            return !entry || typeof entry.title !== 'string' || typeof entry.text !== 'string' ||
              typeof entry.summary !== 'string' || !Array.isArray(entry.subjects) ||
              !entry.subjects.every(function (subject) { return typeof subject === 'string'; }) ||
              !Array.isArray(entry.examCodes) || !entry.examCodes.every(function (code) { return typeof code === 'string'; }) ||
              !['current', 'retired', 'retiring'].includes(entry.status) ||
              !['exam', 'guide', 'page'].includes(entry.kind) ||
              !validPath(entry.url) || (entry.successor && (!validPath(entry.successor.url) || typeof entry.successor.code !== 'string'));
          })) throw new Error('Invalid index');
          prepared = prepareEntries(data.entries);
          return prepared;
        } finally { root.clearTimeout(timeout); }
      })().catch(function (error) { indexPromise = undefined; throw error; });
    }
    return indexPromise;
  }
  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function highlight(node, value, tokens) {
    value.split(/(\s+)/).forEach(function (word) {
      var matched = /\S/.test(word) && tokens.some(function (token) {
        return normalize(word).includes(token);
      });
      node.appendChild(matched ? element('mark', '', word) : document.createTextNode(word));
    });
  }
  function setupSearch(widget) {
    var input = widget.querySelector('input');
    var status = widget.querySelector('[data-search-status]');
    var list = widget.querySelector('[data-search-results]');
    var more = widget.querySelector('[data-search-more]');
    var retry = widget.querySelector('[data-search-retry]');
    var clear = widget.querySelector('[data-search-clear]');
    var examples = widget.querySelector('[data-search-examples]');
    var filters = Array.from(widget.querySelectorAll('[data-search-kind]'));
    var kind = 'all', limit = 8, revision = 0, timer, composing = false;
    function render() {
      var results = searchEntries(prepared, input.value, kind);
      list.replaceChildren();
      results.slice(0, limit).forEach(function (match) {
        var entry = match.entry;
        var item = element('li', 'am-search-result');
        var link = element('a', 'am-search-result__link');
        link.href = entry.url;
        var meta = element('span', 'am-search-result__meta', entry.kind === 'exam' ? 'Exam' : entry.kind === 'guide' ? 'Guide' : 'Page');
        var subjects = entry.subjects.slice().sort(function (a, b) {
          return Number(match.tokens.some(function (token) { return normalize(b).includes(token); })) -
            Number(match.tokens.some(function (token) { return normalize(a).includes(token); }));
        });
        if (subjects.length) meta.appendChild(element('span', '', ' · ' + subjects.slice(0, 2).join(' · ')));
        if (entry.status !== 'current') {
          meta.appendChild(element('span', 'am-search-result__retired',
            entry.status === 'retiring' ? 'Retiring ' + entry.retirementDate : 'Retired · Reference'));
        }
        link.appendChild(meta);
        var title = element('span', 'am-search-result__title');
        highlight(title, entry.title, match.tokens);
        link.appendChild(title);
        var description = element('span', 'am-search-result__description');
        highlight(description, excerpt(entry, match.tokens), match.tokens);
        link.appendChild(description);
        item.appendChild(link);
        if (entry.successor) {
          var successor = element('a', 'am-search-result__successor', 'Explore ' + entry.successor.code + ' →');
          successor.href = entry.successor.url;
          item.appendChild(successor);
        }
        list.appendChild(item);
      });
      status.textContent = results.length ? results.length + (results.length === 1 ? ' result' : ' results') +
        (limit < results.length ? ' · Showing ' + limit : '') : 'No results. Try an exam code or a broader subject.';
      more.hidden = results.length <= limit;
      retry.hidden = true;
      widget.removeAttribute('aria-busy');
    }
    async function update(reset) {
      var current = ++revision;
      if (reset) limit = 8;
      root.clearTimeout(timer);
      clear.hidden = !input.value;
      examples.hidden = normalize(input.value).length >= 2;
      if (normalize(input.value).length < 2) {
        list.replaceChildren(); more.hidden = true; retry.hidden = true;
        widget.removeAttribute('aria-busy');
        status.textContent = input.value ? 'Type at least two characters to search.' : 'Find your next exam, guide or topic.';
        return;
      }
      if (prepared) { render(); return; }
      widget.setAttribute('aria-busy', 'true');
      status.textContent = 'Loading search…';
      retry.hidden = true;
      try {
        await loadIndex();
        if (current === revision) render();
      } catch (_) {
        if (current !== revision) return;
        widget.removeAttribute('aria-busy');
        status.textContent = 'Search couldn’t load. Try again, or browse below.';
        retry.hidden = false;
      }
    }
    input.addEventListener('input', function () {
      if (composing) return;
      root.clearTimeout(timer);
      // Invalidate a pending request as soon as the query changes.
      revision++;
      more.hidden = true;
      timer = root.setTimeout(function () { update(true); }, 60);
    });
    input.addEventListener('compositionstart', function () { composing = true; revision++; });
    input.addEventListener('compositionend', function () { composing = false; update(true); });
    widget.querySelector('form').addEventListener('submit', function (event) {
      event.preventDefault();
      if (composing) return;
      update(false).then(function () { var link = list.querySelector('a'); if (link) link.focus(); });
    });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowDown') {
        var link = list.querySelector('a');
        if (link) { event.preventDefault(); link.focus(); }
      }
    });
    list.addEventListener('keydown', function (event) {
      if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
      var links = Array.from(list.querySelectorAll('a'));
      var index = links.indexOf(document.activeElement) + (event.key === 'ArrowDown' ? 1 : -1);
      event.preventDefault();
      if (index < 0) input.focus();
      else if (links[index]) links[index].focus();
    });
    clear.addEventListener('click', function () { input.value = ''; update(true); input.focus(); });
    retry.addEventListener('click', function () { update(false); });
    more.addEventListener('click', function () {
      var previous = limit; limit += 8; render();
      var link = list.children[previous] && list.children[previous].querySelector('a');
      if (link) link.focus();
    });
    filters.forEach(function (button) {
      button.addEventListener('click', function () {
        kind = button.dataset.searchKind;
        filters.forEach(function (filter) { filter.setAttribute('aria-pressed', String(filter === button)); });
        update(true);
      });
    });
    widget.querySelectorAll('[data-search-example]').forEach(function (button) {
      button.addEventListener('click', function () { input.value = button.dataset.searchExample; update(true); input.focus(); });
    });
    widget.hidden = false;
    update(true);
    return { input: input, update: update };
  }
  var controllers = new Map();
  document.querySelectorAll('[data-am-search]').forEach(function (widget) { controllers.set(widget, setupSearch(widget)); });
  var modal = controllers.get(dialog.querySelector('[data-am-search]'));
  function fitMobileViewport() {
    if (root.visualViewport && root.innerWidth <= 600) {
      dialog.style.setProperty('--am-search-viewport-height', root.visualViewport.height + 'px');
    } else dialog.style.removeProperty('--am-search-viewport-height');
  }
  if (root.visualViewport) root.visualViewport.addEventListener('resize', fitMobileViewport);
  function openSearch(invoker) {
    if (dialog.open) return;
    trigger = invoker || document.activeElement;
    fitMobileViewport();
    dialog.showModal();
    document.documentElement.classList.add('am-search-open');
    modal.input.focus();
    modal.update(false);
    // Warm the index only after the visitor explicitly opens search.
    loadIndex().catch(function () {});
  }
  document.querySelectorAll('[data-search-open]').forEach(function (button) {
    button.hidden = false;
    var hint = button.querySelector('kbd');
    if (hint) hint.textContent = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘ K' : 'Ctrl K';
    button.addEventListener('click', function () { openSearch(button); });
  });
  dialog.querySelector('[data-search-close]').addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('keydown', function (event) {
    // A native search input consumes Escape to clear itself before dialog cancellation.
    if (event.key === 'Escape' && !event.isComposing) { event.preventDefault(); dialog.close(); }
    if (event.key === 'Tab') {
      var controls = Array.from(dialog.querySelectorAll('button, input, a[href]')).filter(function (node) {
        return !node.disabled && node.getClientRects().length > 0;
      });
      var first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  dialog.addEventListener('click', function (event) { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', function () {
    document.documentElement.classList.remove('am-search-open');
    if (trigger && trigger.isConnected) trigger.focus();
  });
  // Close before following a same-page section link so its target can scroll and receive focus.
  dialog.addEventListener('click', function (event) {
    var link = event.target.closest('a');
    if (!link) return;
    dialog.close();
    var destination = new URL(link.href);
    if (destination.pathname === root.location.pathname && destination.hash) {
      var target = document.getElementById(destination.hash.slice(1));
      if (target) {
        target.setAttribute('tabindex', '-1');
        root.setTimeout(function () { target.focus({ preventScroll: true }); }, 0);
      }
    }
  });
  document.addEventListener('keydown', function (event) {
    var target = event.target;
    if ((event.metaKey || event.ctrlKey) && !event.altKey && event.key.toLowerCase() === 'k' &&
        !target.closest('input, textarea, select') && !target.isContentEditable) {
      event.preventDefault(); openSearch();
    }
  });
})(typeof window === 'object' ? window : globalThis);
