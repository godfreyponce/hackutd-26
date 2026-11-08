import { TRACE_WINDOW_MS, DEMO_PREFIX } from '../state.js';
import { h, tag, screenHead, cardHead, empty, count, logRow, offlineLine, miles, ICONS, clockTime, DASH } from './common.js';

// SAME test codes (software/hub/alert_level.py): a test is not a hazard.
const TEST_CODES = new Set(['RWT', 'RMT', 'NPT', 'DMO']);
const LEVEL_TEXT = { info: 'Info', watch: 'Watch', warning: 'Warning', emergency: 'Emergency' };
const SENSOR = 'Box sensor';
const UNAVAILABLE = 'Unavailable while the hub is offline';

const g = (v) => `${v.toFixed(2)} g`;

function where(area, distanceMi) {
  const parts = [area, distanceMi == null ? '' : miles(distanceMi)].filter(Boolean);
  return parts.length ? parts.join(', ') : DASH;
}

function magnitude(headline) {
  const m = /\bM ?(\d+(?:\.\d+)?)\b/.exec(headline) ?? /\bmagnitude (\d+(?:\.\d+)?)\b/i.exec(headline);
  return m ? `M${m[1]}` : null;
}

// "Earthquake, emergency level", or the event alone when its title already says the level.
function hazardName(a) {
  return String(a.event).toLowerCase().includes(a.level) ? a.event : `${a.event}, ${a.level} level`;
}

// The history entry logged with the alert on the Overview banner, which carries the code and distance the banner lacks.
const bannerEntry = (history, ctx) => (ctx.alert ? history.alerts.find((a) => a.at === ctx.alert.at) : undefined);

function activeHazard(history, ctx, logged) {
  const shaking = history.quakes.filter((q) => ctx.now - q.at <= TRACE_WINDOW_MS);
  const peak = shaking.length ? g(Math.max(...shaking.map((q) => q.g))) : DASH;
  const alert = ctx.alert && !TEST_CODES.has(logged?.code) ? ctx.alert : null;

  if (alert) {
    const mag = magnitude(alert.headline);
    return {
      kind: 'alert',
      name: hazardName(alert),
      sub: shaking.length ? 'Official hazard alert, and shaking felt at this home' : 'Official hazard alert showing on Overview',
      level: alert.level,
      facts: [
        { label: 'Type', value: alert.event },
        { label: 'Level', value: LEVEL_TEXT[alert.level], level: alert.level },
        mag && { label: 'Magnitude', value: mag },
        { label: 'Where', value: where(alert.area, logged?.distanceMi ?? null) },
        { label: 'Source', value: alert.source || DASH },
        { label: 'Received', value: clockTime(alert.at) },
        { label: 'Peak shaking at this home', value: peak },
      ].filter(Boolean),
      headline: alert.headline || null,
    };
  }
  if (shaking.length) {
    return {
      kind: 'shaking',
      name: 'Shaking felt at this home',
      sub: 'Shaking felt at this home in the last minute. No hazard alert.',
      // Felt shaking has no official level; it takes the warning tint, like an event on Overview.
      level: 'warning',
      facts: [
        { label: 'Peak shaking at this home', value: peak },
        { label: 'Source', value: SENSOR },
        { label: 'Felt', value: clockTime(shaking[0].at) },
      ],
      headline: null,
    };
  }
  const neverReached = !ctx.connected && ctx.linkAt == null;
  return {
    kind: 'none',
    name: 'No active hazard',
    sub: neverReached ? UNAVAILABLE : 'No hazard alert and no shaking in the last minute',
    level: null,
    facts: [],
    headline: null,
  };
}

function sessionRows(history, logged) {
  const quakes = history.quakes.map((q) => ({
    at: q.at, what: 'Shaking at this home', more: `Peak ${g(q.g)}`, wide: null, tag: null, state: SENSOR, level: null, active: false,
  }));
  const alerts = history.alerts.filter((a) => !TEST_CODES.has(a.code)).map((a) => {
    const active = a === logged;
    return {
      at: a.at,
      what: a.event,
      more: where(a.area, a.distanceMi),
      wide: active ? null : [a.demo && DEMO_PREFIX, a.headline].filter(Boolean).join(' ') || null,
      tag: { text: LEVEL_TEXT[a.level], cls: a.level },
      state: active ? 'Active' : a.source || DASH,
      level: a.level,
      active,
    };
  });
  return [...quakes, ...alerts].sort((a, b) => b.at - a.at);
}

// Pure: what the Disasters screen shows for this history and moment. No DOM.
export function disastersModel(history, ctx) {
  const logged = bannerEntry(history, ctx);
  const active = activeHazard(history, ctx, logged);
  const rows = sessionRows(history, logged);
  const neverReached = !ctx.connected && ctx.linkAt == null;
  return {
    head: { eyebrow: 'Hazards near this home', title: 'Disasters', detail: offlineLine(ctx, active.name) ?? active.name },
    active,
    session: {
      sub: 'Newest first. Test alerts are left out.',
      count: rows.length || null,
      countUnit: rows.length === 1 ? 'event' : 'events',
      rows,
      empty: rows.length ? null : neverReached
        ? { text: UNAVAILABLE, sub: 'Shaking at this home and official hazard alerts show here once it connects.' }
        : { text: 'No disasters this session', sub: 'Shaking at this home and official hazard alerts show here.' },
    },
  };
}

function factList(facts) {
  return h('dl', { class: 'facts' }, facts.map((f) => h('div', {},
    h('dt', {}, f.label),
    h('dd', {}, f.level ? tag(f.value, f.level) : f.value))));
}

export function renderDisasters(root, history, ctx) {
  const m = disastersModel(history, ctx);
  const a = m.active;
  const activeCard = h('section', { class: a.level ? 'card active' : 'card', 'data-level': a.level },
    cardHead(a.kind === 'shaking' ? ICONS.wave : ICONS.alert, 'Active hazard', a.sub),
    a.headline ? h('p', { class: 'headline' }, a.headline) : null,
    a.facts.length ? factList(a.facts) : null);
  const s = m.session;
  const sessionCard = h('section', { class: 'card grow' },
    cardHead(ICONS.wave, 'This session', s.sub, s.count ? count(s.count, s.countUnit) : null),
    s.empty ? empty(s.empty.text, s.empty.sub) : h('ol', { class: 'log' }, s.rows.map(logRow)));
  root.replaceChildren(screenHead(m.head.eyebrow, m.head.title, m.head.detail), activeCard, sessionCard);
}
