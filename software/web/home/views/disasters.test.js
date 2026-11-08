import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialHistory, initialState, record, reduce, activeAlert, TRACE_WINDOW_MS } from '../state.js';
import { clockTime } from './common.js';
import { disastersModel } from './disasters.js';

const T = 1_000_000;

// The sim's `a` key, with the level the hub adds.
const SIM_ALERT = {
  type: 'alert', source: 'usgs', event: 'Earthquake', severity: 'Severe', area: 'Richardson, TX',
  headline: 'M5.1 earthquake near Richardson, TX', code: 'EQW', station: 'HACKDEMO', distance_mi: 3, demo: true, level: 'emergency',
};
const quake = (g) => ({ type: 'quake', peak_g: g });

// Feeds [atMs, msg] pairs through the same reducers app.js uses and builds the ctx it passes.
function screen(events, now, { connected = true, linkAt = T - 60_000 } = {}) {
  let state = initialState();
  let history = initialHistory();
  for (const [at, msg] of events) {
    state = reduce(state, msg, at);
    history = record(history, msg, at);
  }
  return disastersModel(history, { now, connected, linkAt, alert: activeAlert(state, now) });
}

const fact = (m, label) => m.active.facts.find((f) => f.label === label);
const factValue = (m, label) => fact(m, label)?.value;

test('with nothing this session the screen is calm and says so once per card', () => {
  const m = screen([], T);
  assert.equal(m.head.detail, 'No active hazard');
  assert.equal(m.active.kind, 'none');
  assert.equal(m.active.sub, 'No hazard alert and no shaking in the last minute');
  assert.equal(m.active.empty, undefined);
  assert.deepEqual(m.active.facts, []);
  assert.deepEqual(m.session.rows, []);
  assert.equal(m.session.count, null);
  assert.deepEqual(m.session.empty, { text: 'No disasters this session', sub: 'Shaking at this home and official hazard alerts show here.' });
});

test('an official alert on Overview is the active hazard, with its facts', () => {
  const m = screen([[T, SIM_ALERT]], T + 5000);
  assert.equal(m.head.detail, 'Earthquake, emergency level');
  assert.equal(m.active.kind, 'alert');
  assert.equal(m.active.level, 'emergency');
  assert.equal(factValue(m, 'Type'), 'Earthquake');
  assert.deepEqual(fact(m, 'Level'), { label: 'Level', value: 'Emergency', level: 'emergency' });
  assert.equal(factValue(m, 'Magnitude'), 'M5.1');
  assert.equal(factValue(m, 'Where'), 'Richardson, TX, 3 mi away');
  assert.equal(factValue(m, 'Source'), 'USGS');
  assert.equal(factValue(m, 'Received'), clockTime(T));
  assert.equal(factValue(m, 'Peak shaking at this home'), '--');
  assert.equal(m.active.headline, 'DEMO, not a real alert. M5.1 earthquake near Richardson, TX');
});

test('a non demo alert headline has no demo words', () => {
  const m = screen([[T, { ...SIM_ALERT, demo: false }]], T + 1000);
  assert.equal(m.active.headline, 'M5.1 earthquake near Richardson, TX');
});

test('no magnitude is shown when the headline does not state one', () => {
  const m = screen([[T, { ...SIM_ALERT, headline: 'Earthquake near Richardson, TX' }]], T + 1000);
  assert.equal(fact(m, 'Magnitude'), undefined);
});

test('an alert with no distance names only the area, and a missing area is a dash', () => {
  const noDistance = screen([[T, { ...SIM_ALERT, distance_mi: undefined }]], T + 1000);
  assert.equal(factValue(noDistance, 'Where'), 'Richardson, TX');
  const nothing = screen([[T, { ...SIM_ALERT, area: undefined, distance_mi: undefined }]], T + 1000);
  assert.equal(factValue(nothing, 'Where'), '--');
});

test('a distance reads the same as on the Alerts screen: whole miles past 10', () => {
  const m = screen([[T, { ...SIM_ALERT, distance_mi: 42.4 }]], T + 1000);
  assert.equal(factValue(m, 'Where'), 'Richardson, TX, 42 mi away');
  assert.equal(m.session.rows[0].more, 'Richardson, TX, 42 mi away');
});

test('an event title that already names its level is not repeated in the head line', () => {
  const m = screen([[T, { type: 'alert', source: 'nws', event: 'Tornado Warning', code: 'TOR', area: 'Dallas County', level: 'emergency' }]], T + 1000);
  assert.equal(m.head.detail, 'Tornado Warning, emergency level');
  const w = screen([[T, { type: 'alert', source: 'nws', event: 'Flash Flood Warning', code: 'FFW', level: 'warning' }]], T + 1000);
  assert.equal(w.head.detail, 'Flash Flood Warning');
});

test('shaking felt in the last minute fills the peak shaking at this home, the highest reading', () => {
  const m = screen([[T, SIM_ALERT], [T + 1000, quake(0.5)], [T + 2000, quake(0.82)], [T + 3000, quake(0.3)]], T + 10_000);
  assert.equal(factValue(m, 'Peak shaking at this home'), '0.82 g');
});

test('shaking older than the last minute is not part of the active hazard', () => {
  const m = screen([[T, SIM_ALERT], [T + 1000, quake(0.82)]], T + 1000 + TRACE_WINDOW_MS + 1);
  assert.equal(factValue(m, 'Peak shaking at this home'), '--');
});

test('shaking with no official alert says it was felt at this home, from the box sensor, at warning tint', () => {
  const m = screen([[T, quake(0.82)]], T + 5000);
  assert.equal(m.active.kind, 'shaking');
  assert.equal(m.head.detail, 'Shaking felt at this home');
  assert.equal(m.active.level, 'warning');
  assert.equal(factValue(m, 'Peak shaking at this home'), '0.82 g');
  assert.equal(factValue(m, 'Source'), 'Box sensor');
  assert.equal(factValue(m, 'Felt'), clockTime(T));
  assert.equal(fact(m, 'Level'), undefined);
  assert.equal(fact(m, 'Magnitude'), undefined);
});

test('a minute after the shaking stops there is no active hazard again', () => {
  const m = screen([[T, quake(0.82)]], T + TRACE_WINDOW_MS + 1);
  assert.equal(m.active.kind, 'none');
  assert.equal(m.active.level, null);
  assert.equal(m.head.detail, 'No active hazard');
  assert.equal(m.session.rows.length, 1);
});

test('a test alert on Overview is not an active hazard', () => {
  const m = screen([[T, { type: 'alert', source: 'nws', event: 'Required Weekly Test', code: 'RWT', level: 'info' }]], T + 1000);
  assert.equal(m.active.kind, 'none');
  assert.equal(m.head.detail, 'No active hazard');
});

test('the session timeline merges shaking and hazard alerts newest first and skips test alerts', () => {
  const m = screen([
    [T, quake(0.5)],
    [T + 1000, { type: 'alert', source: 'nws', event: 'Required Monthly Test', code: 'RMT', level: 'info' }],
    [T + 2000, SIM_ALERT],
    [T + 3000, { type: 'alert', source: 'nws', event: 'Demo Warning', code: 'DMO', demo: true, level: 'info' }],
    [T + 4000, quake(0.82)],
    [T + 5000, { type: 'alert', source: 'nws', event: 'Tornado Watch', code: 'TOA', area: 'Dallas County', headline: 'Tornado watch until 9 PM', level: 'watch' }],
  ], T + 6000);
  assert.deepEqual(m.session.rows.map((r) => r.what), ['Tornado Watch', 'Shaking at this home', 'Earthquake', 'Shaking at this home']);
  const [watch, felt, eq] = m.session.rows;
  assert.deepEqual(watch, {
    at: T + 5000, what: 'Tornado Watch', more: 'Dallas County', wide: 'Tornado watch until 9 PM',
    tag: { text: 'Watch', cls: 'watch' }, state: 'NWS', level: 'watch', active: false,
  });
  assert.deepEqual(felt, {
    at: T + 4000, what: 'Shaking at this home', more: 'Peak 0.82 g', wide: null, tag: null, state: 'Box sensor', level: null, active: false,
  });
  // The watch ranks below the earthquake, so the earthquake stays on the Overview banner.
  assert.deepEqual([eq.more, eq.tag, eq.level, eq.active], ['Richardson, TX, 3 mi away', { text: 'Emergency', cls: 'emergency' }, 'emergency', true]);
  assert.equal(m.session.count, 4);
  assert.equal(m.session.countUnit, 'events');
  assert.equal(m.session.empty, null);
});

test('the row for the alert on the Overview banner is active and leaves its headline to the card above', () => {
  const m = screen([[T, { ...SIM_ALERT, headline: 'Earthquake felt', code: 'EQA', level: 'watch' }], [T + 1000, SIM_ALERT]], T + 2000);
  const [now, before] = m.session.rows;
  assert.deepEqual([now.active, now.state, now.wide], [true, 'Active', null]);
  assert.deepEqual([before.active, before.state, before.wide], [false, 'USGS', 'DEMO, not a real alert. Earthquake felt']);
});

test('one event is counted in the singular', () => {
  const m = screen([[T, quake(0.5)]], T + 1000);
  assert.deepEqual([m.session.count, m.session.countUnit], [1, 'event']);
});

test('a timeline with only test alerts is still empty', () => {
  const m = screen([[T, { type: 'alert', source: 'nws', event: 'Required Weekly Test', code: 'RWT', level: 'info' }]], T + 1000);
  assert.deepEqual(m.session.rows, []);
  assert.equal(m.session.empty.text, 'No disasters this session');
});

test('with the hub link lost the head line says so and names the last known hazard', () => {
  const m = screen([[T, SIM_ALERT]], T + 5000, { connected: false, linkAt: T + 2000 });
  assert.equal(m.head.detail, 'Hub offline. Last known: earthquake, emergency level');
  assert.equal(m.active.sub, 'Official hazard alert showing on Overview');
  assert.equal(m.session.sub, 'Newest first. Test alerts are left out.');
  assert.equal(m.session.rows.length, 1);
  const quiet = screen([], T, { connected: false, linkAt: T });
  assert.equal(quiet.head.detail, 'Hub offline. Last known: no active hazard');
  assert.equal(quiet.session.empty.text, 'No disasters this session');
});

test('with the hub never reached nothing is claimed', () => {
  const m = screen([], T, { connected: false, linkAt: null });
  assert.equal(m.head.detail, 'Hub offline. Nothing received yet');
  assert.equal(m.active.kind, 'none');
  assert.equal(m.active.sub, 'Unavailable while the hub is offline');
  assert.equal(m.session.count, null);
  assert.equal(m.session.empty.text, 'Unavailable while the hub is offline');
  assert.doesNotMatch(JSON.stringify(m), /since|last known|No disasters/i);
});

test('no wording on the screen names a fall, 911, an em dash or a middle dot, online or offline', () => {
  const busy = [[T, SIM_ALERT], [T + 1000, quake(0.82)]];
  for (const opts of [{}, { connected: false, linkAt: T + 1500 }, { connected: false, linkAt: null }]) {
    for (const [events, now] of [[busy, T + 2000], [[], T], [[[T, quake(0.4)]], T + 1000]]) {
      assert.doesNotMatch(JSON.stringify(screen(events, now, opts)), /fall|911|·|—/i);
    }
  }
});
