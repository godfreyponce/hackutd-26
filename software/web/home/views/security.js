import { h, tag, count, logRow, screenHead, cardHead, empty, offlineLine, clockTime, ago, DASH, ICONS } from './common.js';
import { liveness } from '../state.js';

const PRESENCE_WORD = { moving: 'Moving', still: 'Still', none: 'Nobody seen' };
const PRESENCE_LINE = { moving: 'Someone is moving', still: 'Someone is still', none: 'Nobody seen' };
// fall_hint is the internal name; the screen says what happened, never "fall".
// A hint claims no check-in: the agent ignores it while one is open, and it may be down.
const STILL_NOTE = 'This can start a check-in.';
const EVENT = {
  help_gesture: { what: 'Help sign seen', more: 'The camera saw the HELP sign.', tag: { text: 'Help sign', cls: 'danger' } },
  fall_hint: { what: 'Still after moving', more: STILL_NOTE, tag: null },
};

const eventWords = (e) => (e.kind === 'presence' ? { what: PRESENCE_WORD[e.state], more: '', tag: null } : EVENT[e.kind]);

// The sim sends presence only on a key press, so a quiet feed is not a warning: it says when it last spoke.
function feed(seenAt, now, ctx, unknown) {
  if (seenAt == null) return { text: unknown, cls: '' };
  if (ctx.connected && liveness(seenAt, now) === 'live') return { text: 'Live', cls: 'ok', pill: true };
  return { text: `Last update ${ago(seenAt, now)}`, cls: '', pill: true };
}

// A session count with the time of the newest one. Before the hub is ever reached it is unknown, not zero.
function tally({ count: n, last }, known) {
  return {
    sub: 'Counted this session',
    value: known ? String(n) : DASH,
    muted: !known || n === 0,
    facts: [{ label: 'Last', text: last == null ? DASH : clockTime(last) }],
  };
}

// Everything the Security screen says, from the session history. No DOM, so node tests can read it.
export function securityModel(history, ctx) {
  const { now } = ctx;
  const known = ctx.connected || ctx.linkAt != null;
  const p = history.presence;
  const online = p ? PRESENCE_LINE[p.state] : 'No presence data yet';

  return {
    eyebrow: 'Presence and camera',
    title: 'Security',
    detail: offlineLine(ctx, p ? online : null) ?? online,
    presence: {
      title: 'Presence now',
      sub: 'From the presence feed',
      word: p ? PRESENCE_WORD[p.state] : DASH,
      muted: !p,
      facts: [
        { label: 'Since', text: p ? clockTime(p.since) : DASH },
        { label: 'Feed', ...feed(history.seen.presence, now, ctx, ctx.connected ? 'Waiting' : DASH) },
      ],
      note: 'The camera service repeats its state every 5 s. Sim keys send only on change.',
    },
    help: { title: 'Help sign', ...tally(history.helpSigns, known), note: 'The camera repeats it while the sign is held.' },
    still: { title: 'Still after moving', ...tally(history.stillHints, known), note: STILL_NOTE },
    events: {
      title: 'Events',
      sub: 'This session, newest first',
      count: known && history.security.length ? history.security.length : null,
      rows: history.security.map((e) => ({ at: e.at, ...eventWords(e) })),
      empty: known
        ? { text: 'No events yet', sub: 'Presence changes and help signs show here.' }
        : { text: 'Unavailable while the hub is offline', sub: '' },
    },
  };
}

const PERSON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="6" r="3"/><path d="M5 21v-3a7 7 0 0 1 14 0v3"/></svg>';
const HAND = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 13V5.5a1.5 1.5 0 0 1 3 0V12M11 11V4a1.5 1.5 0 0 1 3 0v7M14 11V5.5a1.5 1.5 0 0 1 3 0V14c0 4-2.5 7-6 7-2.5 0-4-1.2-5.3-3.2L3.5 14a1.5 1.5 0 0 1 2.6-1.5L8 15"/></svg>';
const PAUSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M10 9v6M14 9v6"/></svg>';

const facts = (list) => h('dl', { class: 'facts' }, list.map((f) =>
  h('div', {}, h('dt', {}, f.label), h('dd', {}, f.pill ? tag(f.text, f.cls) : f.text))));

const card = (icon, c, big) => h('section', { class: 'card' },
  cardHead(icon, c.title, c.sub),
  h('div', { class: `sec-big${c.muted ? ' muted' : ''}` }, big),
  facts(c.facts),
  h('div', { class: 'card-note' }, c.note));

export function renderSecurity(root, history, ctx) {
  const m = securityModel(history, ctx);
  const { events } = m;

  const log = events.rows.length
    ? h('ol', { class: 'log' }, events.rows.map((r) => logRow({ at: r.at, what: r.what, more: r.more, tag: r.tag })))
    : empty(events.empty.text, events.empty.sub);

  root.replaceChildren(
    screenHead(m.eyebrow, m.title, m.detail),
    h('div', { class: 'sec-cards' }, card(PERSON, m.presence, m.presence.word), card(HAND, m.help, m.help.value), card(PAUSE, m.still, m.still.value)),
    h('section', { class: 'card grow' },
      cardHead(ICONS.shield, events.title, events.sub, events.count == null ? null : count(events.count, events.count === 1 ? 'event' : 'events')),
      log),
  );
}
