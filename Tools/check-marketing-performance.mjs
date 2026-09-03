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
console.log('Performance contracts passed: analytics, CSS reference, JS syntax, lazy images, cache safety.');
