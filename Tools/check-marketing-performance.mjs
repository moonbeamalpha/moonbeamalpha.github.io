#!/usr/bin/env node
// Dependency-free contracts for the lightweight homepage and asset-only cache.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = path => readFileSync(resolve(root, path), 'utf8');
function htmlFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') return [];
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? htmlFiles(path) : entry.name.endsWith('.html') ? [path] : [];
  });
}
for (const path of htmlFiles(root)) {
  const html = readFileSync(path, 'utf8');
  assert(!(html.includes('GTM-TK79R26R') && html.includes('G-YTN7LFS04Y')), `Duplicate analytics: ${path}`);
}
const home = read('index.html');
assert(home.includes('href="/home.min.css"'), 'Homepage must use the generated CSS bundle');
assert(!/src="[^"\n]*(?:gsap|ScrollTrigger)/i.test(home), 'Animation libraries returned to the critical path');
assert(!/html\.js/.test(read('home.css')), 'Do not hide initial content behind a JS marker');
for (const [, attributes, source] of home.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) {
  if (!/type="application\/ld\+json"/.test(attributes)) new vm.Script(source);
}
new vm.Script(read('theme.js'));
const entranceScript = home.match(/\(function initEntranceAnimations\(\) \{[\s\S]*?\n        \}\)\(\);/)?.[0];
assert(entranceScript, 'Native entrance animations are missing');
assert(entranceScript.includes("'.hero-devices > .phone-wrap'"), 'Only decorative hero phones should animate');
assert(!/hero-text|hero-ctas|hero-app-title/.test(entranceScript), 'Never gate hero copy on an entrance');
assert(entranceScript.includes('motionPreference.matches'), 'Entrance animations must respect reduced motion');
assert(entranceScript.includes('heroObserver.unobserve(entry.target)'), 'Hero entrance must run once');
assert(entranceScript.includes("remove('hero-phone-enter')"), 'Clean up completed hero animation layers');
const phoneKeyframes = read('home.css').match(/@keyframes hero-phone-settle \{[\s\S]*?\n    \}/)?.[0];
assert(phoneKeyframes && /translate:/.test(phoneKeyframes));
assert(!/opacity:|filter:|transform:|width:|height:/.test(phoneKeyframes), 'Hero settling must preserve visibility, angles and layout');
assert(/\.reveal-in\.reveal-after-device\s*\{\s*animation-delay: 160ms;/.test(read('home.css')));
assert(!/\.reveal-pending\s*\{[^}]*opacity:\s*0/.test(read('home.css')), 'Reveals must be additive, not opacity:0 by default');
for (const source of [read('home.css'), read('theme-light.css')]) {
  for (const [, selectors, declarations] of source.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    if (selectors.split(',').some(selector => /\.(mac|ipad)-wrap$/.test(selector.trim()))) {
      assert(!declarations.includes('drop-shadow('), 'Do not filter the Mac/iPad wrapper surfaces');
    }
  }
}
assert(/\.ipad-slide\s*\{[^}]*visibility:\s*hidden/.test(read('home.css')));
assert(/\.ipad-slide\.active\s*\{[^}]*visibility:\s*visible/.test(read('home.css')));

// Exercise the actual inline counter implementation without a browser or any
// copied catalogue totals: final values must come from generated HTML.
const counterScript = home.match(/\(function initMetricCounters\(\) \{[\s\S]*?\n        \}\)\(\);/)?.[0];
assert(counterScript, 'Native metric count-up is missing');
const metricValues = [...home.matchAll(/class="metric-number[^>]*>([^<]+)<\/span>/g)].map(match => match[1]);
assert(metricValues.length > 0);
function setupCounters(reduce = false, supportsObserver = true) {
  const preference = { matches: reduce };
  const frames = [];
  const observed = new Set();
  let notify;
  const elements = metricValues.map(textContent => ({
    textContent, style: {}, children: [],
    getBoundingClientRect: () => ({ width: 100 }),
    replaceChildren(...children) { this.children = children; }
  }));
  function Observer(callback) {
    notify = callback;
    this.observe = element => observed.add(element);
    this.unobserve = element => observed.delete(element);
  }
  const window = { matchMedia: () => preference, requestAnimationFrame: callback => frames.push(callback) };
  if (supportsObserver) window.IntersectionObserver = Observer;
  vm.runInNewContext(counterScript, {
    window, IntersectionObserver: Observer,
    document: {
      querySelectorAll: () => elements,
      createElement: () => ({ setAttribute(name, value) { this[name] = value; } })
    }
  });
  return { elements, preference, frames, observed, notify };
}
const counters = setupCounters();
assert.equal(counters.frames.length, 0, 'No counter work before entering the viewport');
const first = counters.elements[0];
counters.notify([{ target: first, isIntersecting: false }]);
assert.equal(counters.frames.length, 0);
counters.notify([{ target: first, isIntersecting: true }]);
assert(!counters.observed.has(first), 'Only animate once per visit');
counters.frames.shift()(0);
assert.equal(first.children[1].textContent, '0');
counters.frames.shift()(600);
assert(Number(first.children[1].textContent) > 0 && Number(first.children[1].textContent) < Number(metricValues[0]));
counters.frames.shift()(1200);
assert.equal(first.children[1].textContent, metricValues[0]);
assert.equal(first.children[0].textContent, metricValues[0], 'Accessible total must stay stable');
assert.equal(first.children[1]['aria-hidden'], 'true');
assert.equal(counters.frames.length, 0);
assert.equal(setupCounters(true).observed.size, 0, 'Respect reduced motion');
assert.equal(setupCounters(false, false).observed.size, 0, 'Keep static totals without IntersectionObserver');
const interrupted = setupCounters();
interrupted.notify([{ target: interrupted.elements[0], isIntersecting: true }]);
interrupted.preference.matches = true;
interrupted.frames.shift()(0);
assert.equal(interrupted.elements[0].children[1].textContent, metricValues[0]);
assert.equal(interrupted.frames.length, 0);

const fallback = [...home.matchAll(/<noscript>([\s\S]*?)<\/noscript>/g)].map(match => match[1]).join('\n');
for (const [, path] of home.matchAll(/data-theme-bg-(?:dark|light)="([^"]+)"/g)) {
  assert(existsSync(resolve(root, '.' + path)), `Missing lazy image: ${path}`);
}
for (const [, path] of home.matchAll(/<div[^>]+data-theme-bg-dark="([^"]+)"/g)) {
  assert(fallback.includes(`url('${path}')`), `Missing no-JavaScript fallback: ${path}`);
}

const handlers = new Map();
const entries = new Map();
const deleted = [];
const response = (body, ok = true) => ({ body, ok, type: 'basic', clone() { return response(body, ok); } });
let network = async () => response('first');
let storageUnavailable = false;
const cache = {
  match: async request => entries.get(request.url),
  put: async (request, value) => { entries.set(request.url, value); }
};
const worker = {
  location: { origin: 'https://azuremastery.app' },
  addEventListener: (name, handler) => handlers.set(name, handler),
  skipWaiting: async () => {},
  clients: { claim: async () => {} }
};
vm.runInNewContext(read('sw.js'), {
  self: worker, URL, Set,
  fetch: request => network(request),
  caches: {
    open: async () => {
      if (storageUnavailable) throw new Error('storage unavailable');
      return cache;
    },
    keys: async () => ['azure-mastery-static-old', 'azure-mastery-static-v1', 'unrelated'],
    delete: async key => { deleted.push(key); }
  }
});
let activation;
handlers.get('activate')({ waitUntil: promise => { activation = promise; } });
await activation;
assert.deepEqual(deleted, ['azure-mastery-static-old']);
async function request(destination = 'image', url = 'https://azuremastery.app/images/test.webp', method = 'GET') {
  let result;
  const pending = [];
  handlers.get('fetch')({
    request: { destination, url, method },
    respondWith: promise => { result = promise; },
    waitUntil: promise => pending.push(promise)
  });
  const value = await result;
  await Promise.all(pending);
  return value;
}
assert.equal((await request()).body, 'first');
network = async () => response('updated');
assert.equal((await request()).body, 'first', 'Repeat visit must use the cached image');
assert.equal(entries.values().next().value.body, 'updated', 'Refresh must update the cache');
network = async () => { throw new Error('offline'); };
assert.equal((await request()).body, 'updated', 'Cached images should survive network failure');
for (const destination of ['document', 'style', 'script', 'empty']) {
  assert.equal(await request(destination), undefined, `${destination} must not be intercepted`);
}
assert.equal(await request('image', 'https://example.com/image.webp'), undefined);
assert.equal(await request('image', 'https://azuremastery.app/image.webp', 'POST'), undefined);
network = async () => response('missing', false);
assert.equal((await request('font', 'https://azuremastery.app/missing.woff2')).ok, false);
assert(!entries.has('https://azuremastery.app/missing.woff2'), 'Do not cache failed responses');
network = async () => response('fresh');
cache.put = async () => { throw new Error('quota'); };
assert.equal((await request('image', 'https://azuremastery.app/new.webp')).body, 'fresh');
cache.match = async () => { throw new Error('cache read failed'); };
assert.equal((await request()).body, 'fresh');
storageUnavailable = true;
assert.equal((await request()).body, 'fresh');
console.log('Performance contracts passed: analytics, CSS reference, JS syntax, counters, device layers, lazy images, cache safety.');
