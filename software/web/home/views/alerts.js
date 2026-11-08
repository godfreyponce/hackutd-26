import { h, screenHead, cardHead, empty, count, logRow, offlineLine, miles, ICONS } from './common.js';
import { DEMO_PREFIX } from '../state.js';

const LEVEL_TEXT = { info: 'Info', watch: 'Watch', warning: 'Warning', emergency: 'Emergency' };
// What started a check-in, in Overview's words. A check-in with no event on record (a page loaded
// mid-run, or one after a reset) still followed some event, as Overview's "Event detected" says.
const TRIGGER_TEXT = { quake: 'Shaking', help_gesture: 'Help sign seen', fall_hint: 'Still after moving', alert: 'Official alert' };
const OUTCOME = {
  asking: { text: 'Checking in', cls: 'watch' },
  no_answer: { text: 'No response', cls: 'warning' },
  help: { text: 'Contacting help', cls: 'danger' },
  alarm: { text: 'Contacting help', cls: 'danger' },
  ok: { text: 'Okay', cls: 'ok' },
  clear: { text: 'Cleared', cls: 'ok' },
};
const UNAVAILABLE = 'Unavailable while the hub is offline';

const tally = (n, one, many) => (n ? { n, unit: n === 1 ? one : many } : null);

// Rows not on the banner carry no state: an alert outranked on the banner may still be in effect.
function alertRow(a, shownAt) {
  const active = a.at === shownAt;
  return {
    at: a.at,
    what: [a.source, a.event].filter(Boolean).join(' '),
    more: [a.area, a.distanceMi == null ? null : miles(a.distanceMi)].filter(Boolean).join(', ') || null,
    wide: (a.demo ? [DEMO_PREFIX, a.headline] : [a.headline]).filter(Boolean).join(' ') || null,
    tag: { text: LEVEL_TEXT[a.level] ?? a.level, cls: a.level },
    level: a.level,
    active,
    state: active ? 'Active' : null,
  };
}

function checkinRow(c) {
  const transcript = c.heard?.transcript?.trim();
  const asked = c.tries === 1 ? 'Asked once' : `Asked ${c.tries} times`;
  // An okay or a clear after help was contacted keeps that fact, since the tag only shows the last state.
  const helpedThenEnded = c.escalated && (c.state === 'ok' || c.state === 'clear');
  // Help stays contacted until ok or clear, like Overview; a stand-up question after the alarm does not lower it.
  const standUp = c.escalated && (c.state === 'asking' || c.state === 'no_answer');
  return {
    at: c.at,
    what: TRIGGER_TEXT[c.trigger] ?? 'Event detected',
    more: helpedThenEnded ? `${asked}. Escalated to Contacting help.` : standUp ? `${asked}. Stand-up question asked.` : asked,
    wide: transcript ? `Heard "${transcript}"` : null,
    tag: standUp ? OUTCOME.alarm : OUTCOME[c.state],
  };
}

// What is happening now: the alert on the Overview banner and how the latest check-in stands.
function nowLine(shown, latest, anyAlerts) {
  const parts = [shown && `${shown.what} showing`, latest && `Latest check-in: ${latest.tag.text}`].filter(Boolean);
  if (parts.length) return parts.join('. ');
  return anyAlerts ? 'No alert showing now' : 'No alerts or check-ins yet';
}

// Everything the Alerts screen shows, as plain data and wording. No DOM.
export function alertsModel(history, ctx) {
  const neverReached = !ctx.connected && ctx.linkAt == null;
  const alerts = history.alerts.map((a) => alertRow(a, ctx.alert?.at));
  const checkins = history.checkins.map(checkinRow);
  const shown = alerts.find((r) => r.active);
  const now = nowLine(shown, checkins[0], alerts.length > 0);
  return {
    eyebrow: 'Official alerts and check-ins',
    title: 'Alerts',
    detail: offlineLine(ctx, now) ?? now,
    alerts: {
      title: 'Official alerts',
      sub: shown ? `${shown.what} is showing on Overview` : 'Newest first',
      count: tally(alerts.length, 'alert', 'alerts'),
      rows: alerts,
      empty: { text: neverReached ? UNAVAILABLE : 'No official alerts yet', sub: 'Alerts the hub receives show here' },
    },
    checkins: {
      title: 'Check-ins',
      sub: 'Newest first',
      count: tally(checkins.length, 'check-in', 'check-ins'),
      rows: checkins,
      empty: { text: neverReached ? UNAVAILABLE : 'No check-ins yet', sub: 'After an event the box asks if you are okay' },
      note: 'Demo alarm. No emergency number is called.',
    },
  };
}

function card(cls, icon, part) {
  return h('div', { class: `card grow ${cls}` },
    cardHead(icon, part.title, part.sub, part.count && count(part.count.n, part.count.unit)),
    part.rows.length ? h('ol', { class: 'log' }, part.rows.map(logRow)) : empty(part.empty.text, part.empty.sub),
    part.note ? h('div', { class: 'card-note' }, part.note) : null);
}

export function renderAlerts(root, history, ctx) {
  const m = alertsModel(history, ctx);
  root.replaceChildren(
    screenHead(m.eyebrow, m.title, m.detail),
    h('div', { class: 'alerts-grid' },
      card('official', ICONS.alert, m.alerts),
      card('checkins', ICONS.chat, m.checkins)));
}
