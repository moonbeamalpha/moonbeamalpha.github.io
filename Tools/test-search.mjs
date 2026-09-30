#!/usr/bin/env node
// Execute the actual matcher against the generated public corpus and semantic fixtures.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { performance } from 'node:perf_hooks';
import { gzipSync } from 'node:zlib';
const require = createRequire(import.meta.url);
const { normalize, prepareEntries, searchEntries, excerpt } = require('../search.js');
const bytes = readFileSync(new URL('../data/search-index.json', import.meta.url));
const index = JSON.parse(bytes);
const corpus = prepareEntries(index.entries);
const results = (query, kind = 'all') => searchEntries(corpus, query, kind);
const first = query => results(query)[0]?.entry.url;
for (const query of ['AZ-104', 'az104', 'AZ 104', 'az–104', 'ÁZ-104']) assert.equal(first(query), '/exams/az-104/');
for (const query of ['AZ-105', 'AZ-999', 'SC-301', 'AI-104']) assert.equal(results(query).length, 0, `Never correct exam digits: ${query}`);
assert.equal(first('networking'), '/exams/az-700/');
assert.equal(first('Fabric'), '/exams/dp-700/');
assert.equal(first('PowerBI'), '/exams/pl-300/');
assert.equal(first('M365'), '/exams/ab-900/');
assert.equal(first('identity administrator'), '/exams/sc-300/');
assert.equal(first('azure administr'), '/exams/az-104/');
assert.equal(first('Ask Aura'), '/#ask-aura');
assert.equal(first('privacy policy'), '/apps/AzureMastery/privacy.html');
assert.equal(first('securty'), first('security'));
assert.equal(first('netwrok'), first('network'));
assert(results('security').some(r => r.entry.kind === 'exam'));
assert(results('security').some(r => r.entry.kind === 'guide'));
assert(results('security').some(r => r.entry.kind === 'page'));
for (const kind of ['exam', 'guide', 'page']) assert(results('security', kind).every(r => r.entry.kind === kind));
const retired = results('AZ500')[0].entry;
assert.equal(retired.status, 'retired');
assert.equal(retired.successor.code, 'SC-500');
assert.equal(retired.successor.url, '/exams/sc-500/');
const broad = results('security');
assert(broad.findIndex(r => r.entry.status !== 'current') > broad.findLastIndex(r => r.entry.status === 'current'));
for (const query of ['', 'a', '  ', 'the and', '<script>alert(1)</script>', 'xxxxzzzz']) assert.equal(results(query).length, 0);
assert.equal(normalize('M365 PowerBI'), 'microsoft 365 power bi');
assert.equal(index.version, 1);
assert.equal(new Set(index.entries.map(e => e.url)).size, index.entries.length);
assert(gzipSync(bytes).length <= 150 * 1024);

// A topic late in page text must remain searchable; combined terms must all match.
const fixtures = prepareEntries([
  {url:'/topic/',title:'Cloud design',kind:'guide',subjects:[],headings:'',summary:'Design a service.',text:'Private endpoints and availability zones',examCodes:[],status:'current'},
  {url:'/other/',title:'Cloud storage',kind:'exam',subjects:[],headings:'',summary:'Storage.',text:'Private containers',examCodes:[],status:'current'},
]);
assert.deepEqual(searchEntries(fixtures, 'private zones').map(r => r.entry.url), ['/topic/']);
assert(excerpt(fixtures[0].entry, ['zones']).includes('availability zones'));
assert.equal(searchEntries(fixtures, 'availability nonexistent').length, 0);

const queries = ['AZ104', 'security', 'networking', 'Fabric', 'PowerBI', 'M365', 'securty', 'xxxxzzzz', 'identity administrator'];
const timings = [];
for (let run = 0; run < 10; run++) for (const query of queries) {
  const start = performance.now(); results(query); timings.push(performance.now() - start);
}
timings.sort((a,b) => a-b);
const p95 = timings[Math.floor(timings.length * .95)];
assert(p95 < 100, `Search p95 ${p95.toFixed(1)}ms exceeds 100ms`);
console.log(`Search contracts passed: ${index.entries.length} destinations; matching, lifecycle, filters, excerpts; p95 ${p95.toFixed(1)}ms.`);
