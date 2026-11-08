import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialHistory, record, liveness, HISTORY_MAX, LIVE_MS } from './state.js';

const T = 1_000_000;

// Each message arrives one second after the one before it.
function run(...msgs) {
  return msgs.reduce((h, m, i) => record(h, m, T + i * 1000), initialHistory());
}

const asking = (n) => ({ type: 'checkin', state: 'asking', try: n });
const checkin = (state, n = 1) => ({ type: 'checkin', state, try: n });

test('starts empty, with nothing seen', () => {
  const h = initialHistory();
  assert.deepEqual([h.alerts, h.checkins, h.quakes, h.security], [[], [], [], []]);
  assert.equal(h.presence, null);
  assert.equal(h.power, null);
  assert.equal(h.battery, null);
  assert.deepEqual(h.seen, {});
});

test('alerts are logged newest first with the level the hub added', () => {
  const h = run(
    { type: 'alert', source: 'noaa', event: 'Tornado Watch', area: 'Dallas County', code: 'TOA', level: 'watch' },
    { type: 'alert', source: 'usgs', event: 'Earthquake', area: 'Richardson, TX', headline: 'M5.1 near Richardson', code: 'EQW', station: 'HACKDEMO', distance_mi: 3, demo: true, level: 'emergency', severity: 'Severe' },
  );
  assert.equal(h.alerts.length, 2);
  assert.deepEqual(h.alerts[0], {
    at: T + 1000, source: 'USGS', event: 'Earthquake', level: 'emergency', severity: 'Severe', area: 'Richardson, TX',
    headline: 'M5.1 near Richardson', code: 'EQW', station: 'HACKDEMO', distanceMi: 3, demo: true,
  });
  assert.equal(h.alerts[1].event, 'Tornado Watch');
  assert.equal(h.alerts[1].level, 'watch');
});

test('a logged alert with a missing or unknown level is a warning, like the banner', () => {
  const h = run({ type: 'alert', source: 'nws', event: 'Flood' }, { type: 'alert', source: 'nws', event: 'Flood', level: 'huge' });
  assert.deepEqual(h.alerts.map((a) => a.level), ['warning', 'warning']);
  assert.equal(h.alerts[0].distanceMi, null);
  assert.equal(h.alerts[0].demo, false);
});

test('a check-in is one entry that follows its states to the outcome, with the event that started it', () => {
  const h = run({ type: 'quake', peak_g: 0.82 }, asking(1), checkin('no_answer', 1), asking(2), checkin('ok', 2));
  assert.equal(h.checkins.length, 1);
  assert.deepEqual(h.checkins[0], {
    at: T + 1000, trigger: 'quake', state: 'ok', tries: 2, heard: null, updatedAt: T + 4000, open: false, escalated: false,
  });
});

test('a check-in keeps the last transcript the voice service heard', () => {
  const h = run(asking(1), { type: 'heard', answer: 'help', transcript: 'help me' }, checkin('help', 1), checkin('alarm', 2));
  assert.equal(h.checkins[0].state, 'alarm');
  assert.equal(h.checkins[0].tries, 1, 'the agent sends the alarm as try tries + 1, but it asked once');
  assert.equal(h.checkins[0].trigger, null);
  assert.deepEqual(h.checkins[0].heard, { answer: 'help', transcript: 'help me' });
});

test('a check-in after help is contacted stays one entry through the stand-up re-ask and its clear', () => {
  const h = run({ type: 'fall_hint' }, asking(1), checkin('alarm', 2), asking(1), checkin('clear', 1));
  assert.equal(h.checkins.length, 1);
  assert.equal(h.checkins[0].trigger, 'fall_hint');
  assert.equal(h.checkins[0].state, 'clear');
  assert.equal(h.checkins[0].escalated, true, 'the clear does not hide that help was contacted');
});

test('a new event after a check-in ends starts a new entry, even one that ended with no response', () => {
  // Help signs start the first two, so the alert is outside the agent's quiet window.
  const help = { type: 'help_gesture', source: 'camera' };
  const h = run(help, asking(1), checkin('no_answer', 3), help, asking(1), checkin('ok', 1),
    { type: 'alert', source: 'usgs', event: 'Earthquake', code: 'EQW', level: 'emergency' }, asking(1));
  assert.deepEqual(h.checkins.map((c) => [c.trigger, c.state]), [['alert', 'asking'], ['help_gesture', 'ok'], ['help_gesture', 'no_answer']]);
  assert.equal(h.checkins[2].open, true);
});

test('a check-in state with no entry open starts one, so a mid-run page load still logs it', () => {
  const h = run(checkin('no_answer', 2));
  assert.equal(h.checkins.length, 1);
  assert.equal(h.checkins[0].state, 'no_answer');
  assert.equal(h.checkins[0].tries, 2);
});

test('an unknown check-in state is ignored', () => {
  assert.deepEqual(run(checkin('maybe')).checkins, []);
});

test('quakes are kept for the whole session, newest first, not only the last minute', () => {
  const h = [{ type: 'quake', peak_g: 0.5 }, { type: 'quake', peak_g: 0.82 }]
    .reduce((acc, m, i) => record(acc, m, T + i * 10 * 60_000), initialHistory());
  assert.deepEqual(h.quakes, [{ at: T + 600_000, g: 0.82 }, { at: T, g: 0.5 }]);
});

test('presence logs each change once, and a repeat only refreshes when it was last seen', () => {
  const p = (state) => ({ type: 'presence', state });
  const h = run(p('moving'), p('moving'), p('still'), { type: 'fall_hint' }, p('still'));
  assert.deepEqual(h.presence, { state: 'still', since: T + 2000, at: T + 4000 });
  assert.deepEqual(h.security.map((e) => [e.kind, e.state ?? null]), [['fall_hint', null], ['presence', 'still'], ['presence', 'moving']]);
});

test('an unknown presence state is ignored', () => {
  const h = run({ type: 'presence', state: 'dancing' });
  assert.equal(h.presence, null);
  assert.deepEqual(h.security, []);
});

test('a help sign is a security event', () => {
  const h = run({ type: 'help_gesture', source: 'camera' });
  assert.deepEqual(h.security, [{ at: T, kind: 'help_gesture' }]);
});

test('power and heartbeat battery are kept with when they arrived', () => {
  const h = run({ type: 'power', state: 'battery' }, { type: 'heartbeat', battery_pct: 87 }, { type: 'power', state: 'sideways' });
  assert.deepEqual(h.power, { state: 'battery', at: T });
  assert.deepEqual(h.battery, { pct: 87, at: T + 1000 });
});

test('each message marks its sender as seen', () => {
  const h = run(
    { type: 'heartbeat', battery_pct: 90 }, { type: 'presence', state: 'none' }, { type: 'help_gesture', source: 'camera' },
    { type: 'agent', step: 'PLAN', text: 'x' }, { type: 'heard', answer: 'ok', transcript: 'fine' },
  );
  assert.deepEqual(h.seen, { hub: T + 4000, sensor: T, presence: T + 1000, camera: T + 2000, agent: T + 3000, voice: T + 4000 });
});

test('quake, power and fall_hint count for their senders; say, checkin and handoff count for the agent', () => {
  const h = run({ type: 'quake', peak_g: 0.1 }, { type: 'fall_hint' }, { type: 'say', text: 'hi' }, { type: 'handoff', note: 'x' });
  assert.equal(h.seen.sensor, T);
  assert.equal(h.seen.presence, T + 1000);
  assert.equal(h.seen.agent, T + 3000);
});

test('reset clears the session history but keeps when each sender was last seen', () => {
  const h = run({ type: 'quake', peak_g: 0.82 }, asking(1), { type: 'presence', state: 'moving' }, { type: 'power', state: 'battery' }, { type: 'reset' });
  assert.deepEqual([h.alerts, h.checkins, h.quakes, h.security], [[], [], [], []]);
  assert.equal(h.presence, null);
  assert.equal(h.power, null);
  assert.equal(h.seen.sensor, T + 3000);
  assert.equal(h.seen.agent, T + 1000);
  assert.equal(h.seen.hub, T + 4000);
});

test('a reset after a quake does not hand the old quake to the next check-in', () => {
  const h = run({ type: 'quake', peak_g: 0.82 }, { type: 'reset' }, asking(1));
  assert.equal(h.checkins[0].trigger, null);
});

test('each list keeps at most HISTORY_MAX entries, dropping the oldest', () => {
  const msgs = Array.from({ length: HISTORY_MAX + 5 }, (_, i) => ({ type: 'quake', peak_g: i }));
  const h = run(...msgs);
  assert.equal(h.quakes.length, HISTORY_MAX);
  assert.equal(h.quakes[0].g, HISTORY_MAX + 4);
});

test('unknown or malformed messages change nothing', () => {
  const h0 = initialHistory();
  assert.equal(record(h0, null, T), h0);
  assert.equal(record(h0, 'quake', T), h0);
  assert.deepEqual(record(h0, { type: 'mystery' }, T), { ...h0, seen: { hub: T } });
});

test('a sender is live when last seen within LIVE_MS, stale after, and unknown when never seen', () => {
  assert.equal(liveness(undefined, T), 'unknown');
  assert.equal(liveness(T, T + LIVE_MS), 'live');
  assert.equal(liveness(T, T + LIVE_MS + 1), 'stale');
});

test('a retry stays in its entry even when a held help sign repeats between tries', () => {
  const help = { type: 'help_gesture', source: 'camera' };
  const h = run(help, asking(1), checkin('no_answer', 1), help, asking(2));
  assert.equal(h.checkins.length, 1);
  assert.equal(h.checkins[0].tries, 2);
});

test('three asks then the alarm counts three asks, not four', () => {
  const h = run(asking(1), checkin('no_answer', 1), asking(2), checkin('no_answer', 2), asking(3), checkin('no_answer', 3), checkin('alarm', 4));
  assert.equal(h.checkins[0].tries, 3);
});

test('only an EQW emergency alert can start a check-in, like the agent rule', () => {
  const watch = { type: 'alert', source: 'nws', event: 'Tornado Watch', code: 'TOA', level: 'watch' };
  const eqw = { type: 'alert', source: 'usgs', event: 'Earthquake', code: 'EQW', level: 'emergency' };
  assert.equal(run(watch, asking(1)).checkins[0].trigger, null);
  assert.equal(run(eqw, asking(1)).checkins[0].trigger, 'alert');
});

test('the first event before a check-in is the one that started it', () => {
  const eqw = { type: 'alert', source: 'usgs', event: 'Earthquake', code: 'EQW', level: 'emergency' };
  const h = run({ type: 'quake', peak_g: 0.82 }, eqw, asking(1));
  assert.equal(h.checkins[0].trigger, 'quake');
});

test('an event during a check-in is not credited to the next one', () => {
  const h = run({ type: 'quake', peak_g: 0.8 }, asking(1), { type: 'fall_hint' }, checkin('ok', 1), asking(1));
  assert.deepEqual(h.checkins.map((c) => c.trigger), [null, 'quake']);
});

test('the clear the agent sends right after an okay to the stand-up question ends the same entry', () => {
  const h = run({ type: 'fall_hint' }, asking(1), checkin('no_answer', 1), checkin('alarm', 2), asking(1), checkin('ok', 1), checkin('clear', 1));
  assert.equal(h.checkins.length, 1);
  assert.equal(h.checkins[0].state, 'clear');
  assert.equal(h.checkins[0].escalated, true);
});

test('after the alarm, the stand-up question and its no answer stay in the escalated entry', () => {
  const h = run({ type: 'fall_hint' }, asking(1), checkin('no_answer', 1), asking(2), checkin('no_answer', 2), asking(3), checkin('no_answer', 3),
    checkin('alarm', 4), asking(1), checkin('no_answer', 1));
  assert.equal(h.checkins.length, 1);
  assert.deepEqual([h.checkins[0].state, h.checkins[0].tries, h.checkins[0].open, h.checkins[0].escalated], ['no_answer', 3, true, true]);
});

test('an event after the alarm starts no new entry until the check-in ends, since the agent ignores it', () => {
  const help = { type: 'help_gesture', source: 'camera' };
  const h = run(help, asking(1), checkin('help', 1), checkin('alarm', 2), help, asking(1), checkin('ok', 1), checkin('clear', 1));
  assert.equal(h.checkins.length, 1);
  assert.deepEqual([h.checkins[0].state, h.checkins[0].escalated], ['clear', true]);
});

test('an EQW emergency alert within 300 s of a check-in start is not a trigger, like the agent quiet window', () => {
  const eqw = { type: 'alert', source: 'usgs', event: 'Earthquake', code: 'EQW', level: 'emergency' };
  const h = run({ type: 'quake', peak_g: 0.8 }, asking(1), checkin('ok', 1), eqw, { type: 'help_gesture' }, asking(1));
  assert.deepEqual(h.checkins.map((c) => c.trigger), ['help_gesture', 'quake']);
  const later = [{ type: 'quake', peak_g: 0.8 }, asking(1), checkin('ok', 1)].reduce((acc, m, i) => record(acc, m, T + i * 1000), initialHistory());
  assert.equal(record(record(later, eqw, T + 301_000), asking(1), T + 302_000).checkins[0].trigger, 'alert');
});

test('a check-in started by a help sign does not mute an EQW emergency alert', () => {
  const eqw = { type: 'alert', source: 'usgs', event: 'Earthquake', code: 'EQW', level: 'emergency' };
  const h = run({ type: 'help_gesture' }, asking(1), checkin('ok', 1), eqw, asking(1));
  assert.deepEqual(h.checkins.map((c) => c.trigger), ['alert', 'help_gesture']);
});

test('a pending trigger older than the newest entry update is replaced by a newer trigger', () => {
  const stale = { ...run(asking(1), checkin('no_answer', 1)), trigger: { kind: 'fall_hint', at: T } };
  const h = record(record(stale, { type: 'help_gesture' }, T + 5000), asking(1), T + 6000);
  assert.equal(h.checkins[0].trigger, 'help_gesture');
});

test('help signs and still-after-moving hints are counted for the session past HISTORY_MAX, and reset clears them', () => {
  const p = (i) => ({ type: 'presence', state: i % 2 ? 'moving' : 'still' });
  const msgs = [{ type: 'help_gesture' }, { type: 'fall_hint' }, { type: 'help_gesture' }, ...Array.from({ length: HISTORY_MAX }, (_, i) => p(i))];
  const h = run(...msgs);
  assert.deepEqual(h.helpSigns, { count: 2, last: T + 2000 });
  assert.deepEqual(h.stillHints, { count: 1, last: T + 1000 });
  assert.equal(h.security.some((e) => e.kind !== 'presence'), false, 'the capped log dropped them');
  const r = record(h, { type: 'reset' }, T + 999_000);
  assert.deepEqual([r.helpSigns, r.stillHints], [{ count: 0, last: null }, { count: 0, last: null }]);
});

test('a message type named like an Object property marks no junk sender', () => {
  const h = run({ type: 'constructor' }, { type: '__proto__' }, { type: 'toString' }, { type: 'alert', source: 'constructor', event: 'X' });
  assert.deepEqual(Object.keys(h.seen), ['hub']);
  assert.equal(h.alerts[0].source, 'CONSTRUCTOR');
});
