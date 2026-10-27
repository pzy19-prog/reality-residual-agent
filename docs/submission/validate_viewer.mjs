#!/usr/bin/env node
// Offline DOM/control smoke check for the single-file viewer. No browser/network.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const path = process.argv[2] ?? new URL('./demo_viewer.html', import.meta.url);
const html = fs.readFileSync(path, 'utf8');
assert.doesNotMatch(html, /(?:https?:\/\/|<script[^>]+src=|<link[^>]+href=)/i);
const source = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(source, 'inline script exists');
const rows = html.match(/const episodes=(\[[\s\S]*?\]);const ep=/)?.[1];
assert.ok(rows, 'embedded trace payload exists');
const payload = JSON.parse(rows);
assert.equal(payload.length, 1);
assert.equal(payload[0].decisions.length, 14);
assert.equal(payload[0].source_commit, '87a3124a9a337a525efdf3d5390905df9803114f');

const ids = ['range','table','detail','pos','meta','step','play','pause'];
const elements = Object.fromEntries(ids.map(id => [id, {value:id==='range'?'0':'', textContent:'', innerHTML:'', onclick:null, oninput:null, append(){}}]));
elements.range.max='0';
const document = {
  querySelector(q) { return elements[q.slice(1)]; },
  createElement() { return {value:'',textContent:''}; },
};
let tick = null, cleared = false;
vm.runInNewContext(source, {
  document, Number, String, Object, Math,
  setInterval(fn) { tick=fn; return 7; },
  clearInterval(id) { cleared=(id===7); },
});
assert.match(elements.table.innerHTML, /UPDATE_MODEL_AND_REPLAN/);
assert.match(elements.detail.innerHTML, /PAUSE_AND_REOBSERVE/);
assert.match(elements.meta.textContent, /development scenario SENSOR_STUCK/);
assert.match(elements.detail.innerHTML, /first 4 of 14/);
elements.step.onclick();
assert.equal(elements.range.value, 1);
assert.match(elements.pos.textContent, /2 \/ 14/);
elements.step.onclick();
elements.step.onclick();
assert.equal(elements.range.value, 3);
assert.match(elements.detail.innerHTML, /COMMON_ACTION/);
elements.play.onclick();
assert.equal(typeof tick, 'function');
tick();
assert.equal(elements.range.value, 4);
elements.pause.onclick();
assert.ok(cleared);
elements.range.value = 8;
elements.range.oninput();
assert.match(elements.detail.innerHTML, /No common safe action across passing checks/);
assert.match(elements.detail.innerHTML, /first 4 of 14/);
elements.range.value = 9;
elements.range.oninput();
assert.match(elements.detail.innerHTML, /Recorded policy fault label: BELT_STOP_OR_MOTION_LOSS/);
console.log(`offline viewer controls advanced real embedded trace: ${payload[0].decisions.length} decisions`);
