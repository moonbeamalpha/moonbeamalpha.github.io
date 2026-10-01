import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../app-store-links.js', import.meta.url), 'utf8');
function setup(hostname = 'azuremastery.app', analytics = true) {
  let listener;
  const sent = [];
  const window = analytics ? { gtag: (...args) => sent.push(args) } : {};
  vm.runInNewContext(source, { URL, location: { hostname }, window,
    document: { addEventListener(type, callback) { assert.equal(type, 'click'); listener = callback; } } });
  return { sent, click(href) { listener?.({ target: { closest: () => href ? { href } : null } }); } };
}
const tracking = setup();
tracking.click('https://apps.apple.com/app/id6760594569?ct=site-home-hero&untrusted=secret');
tracking.click('https://apps.apple.com/gb/app/azure-mastery/id6760594569?ct=site-pro-options');
assert.deepEqual(JSON.parse(JSON.stringify(tracking.sent)), [
  ['event', 'app_store_click', { store_campaign: 'site-home-hero', transport_type: 'beacon' }],
  ['event', 'app_store_click', { store_campaign: 'site-pro-options', transport_type: 'beacon' }]
]);
for (const href of [null, 'https://azuremastery.app/?q=private-query',
  'https://apps.apple.com.evil.example/app/id6760594569?ct=site-home-hero',
  'https://apps.apple.com/app/id67605945690?ct=site-home-hero',
  'https://apps.apple.com/app/id6760594569?ct=my%20private%20answer',
  'https://apps.apple.com/app/id6760594569?ct=' + 'x'.repeat(31)]) tracking.click(href);
assert.equal(tracking.sent.length, 2, 'Search, answers, foreign apps and malformed campaigns must not be measured');
for (const hostname of ['localhost', '127.0.0.1']) {
  const local = setup(hostname); local.click('https://apps.apple.com/app/id6760594569?ct=site-home-hero');
  assert.equal(local.sent.length, 0);
}
setup('azuremastery.app', false).click('https://apps.apple.com/app/id6760594569?ct=site-home-hero');
console.log('App Store measurement: placement-only payloads, host/app validation and local/analytics opt-out pass');
