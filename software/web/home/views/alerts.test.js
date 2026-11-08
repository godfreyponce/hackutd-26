import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialHistory, record, reduce, initialState, activeAlert } from '../state.js';
import { alertsModel } from './alerts.js';

const T = 1_000_000;
const MIN = 60_000;

// Feeds the bus messages through the real history and Overview state, one second apart, and returns
// the model as the screen would see it `later` ms after the last message.
function screen(msgs, { later = 0, connected = true, linkAt = T - 5000 } = {}) {
  let h = initialHistory();
  let s = initialState();
  msgs.forEach((m, i) => {
    h = record(h, m, T + i * 1000);
    s = reduce(s, m, T + i * 1000);
  });
  const now = T + Math.max(0, msgs.length - 1) * 1000 + later;
  return alertsModel(h, { now, connected, linkAt, alert: activeAlert(s, now) });
}

const quakeAlert = {
  type: 'alert', source: 'usgs', event: 'Earthquake', code: 'EQW', station: 'HACKDEMO', distance_mi: 3, demo: true,
  area: 'Richardson, TX', headline: 'M5.1 earthquake near Richardson, TX', severity: 'Severe', level: 'emergency',
};
const tornadoWatch = { type: 'alert', source: 'noaa', event: 'Tornado Watch', area: 'Dallas County', code: 'TOA', level: 'watch', headline: 'Tornado watch until 9 PM' };
const asking = (n) => ({ type: 'checkin', state: 'asking', try: n });
const checkin = (state, n = 1) => ({ type: 'checkin', state, try: n });
const neverReached = { connected: false, linkAt: null };

test('an empty session says so once in each card body, with no count', () => {
  const m = screen([]);
  assert.equal(m.detail, 'No alerts or check-ins yet');
  assert.equal(m.alerts.count, null);
  assert.deepEqual(m.alerts.rows, []);
  assert.equal(m.alerts.empty.text, 'No official alerts yet');
  assert.equal(m.checkins.count, null);
  assert.deepEqual(m.checkins.rows, []);
  assert.equal(m.checkins.empty.text, 'No check-ins yet');
});

test('the head says what is happening now: the alert showing and the latest check-in outcome', () => {
  assert.equal(screen([quakeAlert]).detail, 'USGS Earthquake showing');
  assert.equal(screen([asking(1), checkin('ok')]).detail, 'Latest check-in: Okay');
  assert.equal(screen([quakeAlert, asking(1), checkin('help'), checkin('alarm', 2)]).detail,
    'USGS Earthquake showing. Latest check-in: Contacting help');
  assert.equal(screen([tornadoWatch], { later: 31 * MIN }).detail, 'No alert showing now');
});

test('the card heads count rows with a unit, singular for one', () => {
  const m = screen([tornadoWatch, quakeAlert, asking(1), checkin('ok'), { type: 'help_gesture' }, asking(1)]);
  assert.deepEqual(m.alerts.count, { n: 2, unit: 'alerts' });
  assert.deepEqual(m.checkins.count, { n: 2, unit: 'check-ins' });
  const one = screen([quakeAlert, asking(1)]);
  assert.deepEqual(one.alerts.count, { n: 1, unit: 'alert' });
  assert.deepEqual(one.checkins.count, { n: 1, unit: 'check-in' });
});

test('an alert row shows source and event, area and distance, the demo headline like the banner, and its level tag', () => {
  const [row] = screen([quakeAlert]).alerts.rows;
  assert.equal(row.at, T);
  assert.equal(row.what, 'USGS Earthquake');
  assert.equal(row.more, 'Richardson, TX, 3 mi away');
  assert.equal(row.wide, 'DEMO, not a real alert. M5.1 earthquake near Richardson, TX');
  assert.deepEqual(row.tag, { text: 'Emergency', cls: 'emergency' });
  assert.equal(row.level, 'emergency');
});

test('a real alert keeps its plain headline, and an unknown area or distance is left out', () => {
  const [row] = screen([{ type: 'alert', source: 'nws', event: 'Flood Warning', code: 'FLW', level: 'warning', headline: 'Flooding along the creek' }]).alerts.rows;
  assert.deepEqual(row.tag, { text: 'Warning', cls: 'warning' });
  assert.equal(row.wide, 'Flooding along the creek');
  assert.equal(row.more, null);
  const [far] = screen([{ ...tornadoWatch, area: '', distance_mi: 42.4 }]).alerts.rows;
  assert.equal(far.more, '42 mi away');
});

test('only the alert on the Overview banner is active; the others carry no state, since they may still be in effect', () => {
  const m = screen([tornadoWatch, quakeAlert]);
  assert.deepEqual(m.alerts.rows.map((r) => [r.what, r.active, r.state]),
    [['USGS Earthquake', true, 'Active'], ['NOAA Tornado Watch', false, null]]);
  assert.equal(m.alerts.sub, 'USGS Earthquake is showing on Overview');
  const lower = screen([quakeAlert, tornadoWatch]);
  assert.deepEqual(lower.alerts.rows.map((r) => [r.what, r.active]), [['NOAA Tornado Watch', false], ['USGS Earthquake', true]]);
});

test('a watch stops being active once it expires from the Overview banner', () => {
  assert.equal(screen([tornadoWatch], { later: 10 * MIN }).alerts.rows[0].active, true);
  const m = screen([tornadoWatch], { later: 31 * MIN });
  assert.equal(m.alerts.rows[0].active, false);
  assert.equal(m.alerts.rows[0].state, null);
  assert.equal(m.alerts.sub, 'Newest first');
});

test('a check-in row names what started it, the tries, the last thing heard, and the outcome tag', () => {
  const [row] = screen([{ type: 'quake', peak_g: 0.82 }, asking(1), { type: 'heard', answer: 'no_answer', transcript: '' },
    checkin('no_answer', 1), asking(2), { type: 'heard', answer: 'help', transcript: 'help me' }, checkin('help', 2), checkin('alarm', 3)]).checkins.rows;
  assert.equal(row.at, T + 1000);
  assert.equal(row.what, 'Shaking');
  assert.deepEqual(row.tag, { text: 'Contacting help', cls: 'danger' });
  assert.equal(row.more, 'Asked 2 times');
  assert.equal(row.wide, 'Heard "help me"');
});

test('each event and outcome reads in Overview words with its color', () => {
  const rowAfter = (event, ...states) => screen([event, ...states]).checkins.rows[0];
  assert.equal(rowAfter({ type: 'help_gesture', source: 'camera' }, asking(1)).what, 'Help sign seen');
  assert.equal(rowAfter({ type: 'fall_hint' }, asking(1)).what, 'Still after moving');
  assert.equal(rowAfter(quakeAlert, asking(1)).what, 'Official alert');
  assert.equal(screen([asking(1)]).checkins.rows[0].what, 'Event detected');

  const outcome = (...states) => screen(states).checkins.rows[0].tag;
  assert.deepEqual(outcome(asking(1)), { text: 'Checking in', cls: 'watch' });
  assert.deepEqual(outcome(asking(1), checkin('no_answer', 3)), { text: 'No response', cls: 'warning' });
  assert.deepEqual(outcome(asking(1), checkin('help')), { text: 'Contacting help', cls: 'danger' });
  assert.deepEqual(outcome(asking(1), checkin('ok')), { text: 'Okay', cls: 'ok' });
  assert.deepEqual(outcome(asking(1), checkin('alarm', 3), checkin('clear')), { text: 'Cleared', cls: 'ok' });
});

test('a check-in that ended okay after help was contacted keeps that fact under the label', () => {
  const m = screen([asking(1), checkin('no_answer', 1), asking(2), checkin('no_answer', 2), checkin('alarm', 3), checkin('clear')]);
  assert.equal(m.checkins.rows[0].more, 'Asked 2 times. Escalated to Contacting help.');
  assert.equal(screen([asking(1), checkin('ok')]).checkins.rows[0].more, 'Asked once');
});

test('a check-in that ended with nobody answering keeps No response when the next event starts a new one', () => {
  const m = screen([{ type: 'quake', peak_g: 0.5 }, asking(1), checkin('no_answer', 3), { type: 'help_gesture' }, asking(1), checkin('ok')]);
  assert.deepEqual(m.checkins.rows.map((r) => [r.what, r.tag.text, r.more]),
    [['Help sign seen', 'Okay', 'Asked once'], ['Shaking', 'No response', 'Asked 3 times']]);
});

test('after the alarm the check-in stays Contacting help through the stand-up question until ok or clear', () => {
  const tries = [asking(1), checkin('no_answer', 1), asking(2), checkin('no_answer', 2), asking(3), checkin('no_answer', 3), checkin('alarm', 4)];
  for (const after of [[asking(1)], [asking(1), checkin('no_answer', 1)]]) {
    const m = screen([{ type: 'fall_hint' }, ...tries, ...after]);
    assert.equal(m.checkins.rows.length, 1);
    assert.deepEqual(m.checkins.rows[0].tag, { text: 'Contacting help', cls: 'danger' });
    assert.equal(m.checkins.rows[0].more, 'Asked 3 times. Stand-up question asked.');
    assert.equal(m.detail, 'Latest check-in: Contacting help');
  }
  assert.deepEqual(screen([...tries, asking(1), checkin('ok', 1)]).checkins.rows[0].tag, { text: 'Okay', cls: 'ok' });
});

test('a held help sign resent after the alarm starts no second check-in', () => {
  const help = { type: 'help_gesture', source: 'camera' };
  const m = screen([help, asking(1), checkin('help', 1), checkin('alarm', 2), help, asking(1)]);
  assert.deepEqual(m.checkins.rows.map((r) => [r.what, r.tag.text]), [['Help sign seen', 'Contacting help']]);
});

test('the check-ins card says the alarm is a demo, online and offline', () => {
  for (const opts of [{}, { connected: false, linkAt: T }, neverReached]) {
    assert.match(screen([], opts).checkins.note, /^Demo alarm\./);
  }
});

test('a check-in with nothing heard shows no quote line', () => {
  assert.equal(screen([asking(1)]).checkins.rows[0].wide, null);
  assert.equal(screen([asking(1), { type: 'heard', answer: 'no_answer', transcript: '' }]).checkins.rows[0].wide, null);
});

test('when the hub link drops, the head says so with the last known state and the card subs stay put', () => {
  const m = screen([quakeAlert, asking(1)], { connected: false, linkAt: T + 2000 });
  assert.equal(m.detail, 'Hub offline. Last known: USGS Earthquake showing. Latest check-in: Checking in');
  assert.equal(m.alerts.sub, 'USGS Earthquake is showing on Overview');
  assert.equal(m.checkins.sub, 'Newest first');
  assert.equal(m.alerts.rows.length, 1);
});

test('a hub never reached claims nothing: no counts, and both bodies say they are unavailable', () => {
  const m = screen([], neverReached);
  assert.equal(m.detail, 'Hub offline. Nothing received yet');
  assert.deepEqual([m.alerts.count, m.checkins.count], [null, null]);
  assert.equal(m.alerts.empty.text, 'Unavailable while the hub is offline');
  assert.equal(m.checkins.empty.text, 'Unavailable while the hub is offline');
  assert.deepEqual([m.alerts.sub, m.checkins.sub], ['Newest first', 'Newest first']);
});

test('no wording says fall, 911, or that anyone is called, and none uses a middle dot or em dash, online or offline', () => {
  const msgs = [{ type: 'fall_hint' }, asking(1), checkin('no_answer', 3), checkin('alarm', 4), quakeAlert, asking(1)];
  for (const opts of [{}, { connected: false, linkAt: T }, neverReached]) {
    const text = JSON.stringify(screen(opts === neverReached ? [] : msgs, opts)).replace('No emergency number is called.', '');
    assert.doesNotMatch(text, /\bfall\b|911|\bcall/i);
    assert.doesNotMatch(text, /[·—]/);
  }
});
