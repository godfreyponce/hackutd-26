import { h, tag, screenHead, cardHead, offlineLine, clockTime, ago, DASH } from './common.js';
import { liveness } from '../state.js';

const PRESENCE_WORD = { moving: 'Moving', still: 'Still', none: 'Nobody seen' };
const QUIET_IS_NORMAL = 'Quiet between check-ins is normal.';

const REPORTING = { text: 'Reporting', tone: 'ok' };
const NOT_HEARD = { text: 'Not heard yet', tone: '' };
const UNKNOWN = { text: 'Unknown', tone: '' };
// Only the box sensor heartbeat comes on a steady beat in every run (5 s, also in sim), so only its silence warns.
// Presence repeats only from the real camera service; the sim sends it on a key press.
const STALE = {
  sensors: { text: 'No heartbeat', tone: 'warning' },
  presence: { text: 'No recent update', tone: '' },
};

const joinAnd = (names) => (names.length < 2 ? names.join('') : `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`);
const sentence = (s) => s[0].toUpperCase() + s.slice(1);

// The plain data and wording the System screen shows, from the session history and the hub link.
export function systemModel(history, ctx) {
  const { now, connected, linkAt } = ctx;
  const seen = history.seen;
  const beat = (id, at) => {
    if (!connected) return UNKNOWN;
    const l = liveness(at, now);
    return l === 'unknown' ? NOT_HEARD : l === 'live' ? REPORTING : STALE[id];
  };
  const heard = (at) => (!connected ? UNKNOWN : at == null ? NOT_HEARD : { text: 'Heard', tone: '' });

  const parts = [
    {
      id: 'hub', name: 'Hub', role: 'The bus every part talks through',
      status: connected ? { text: 'Connected', tone: 'ok' } : { text: 'Offline', tone: 'warning' },
      facts: [
        { label: connected ? 'Connected since' : 'Offline since', value: linkAt == null ? DASH : clockTime(linkAt) },
        { label: 'Last message', value: ago(seen.hub, now) },
      ],
      note: 'Each last message time is when this screen got it from the hub.',
    },
    {
      id: 'sensors', name: 'Box sensors', role: 'Heartbeat, power and quake',
      status: beat('sensors', seen.sensor),
      facts: [
        { label: 'Last message', value: ago(seen.sensor, now) },
        { label: 'Battery', value: history.battery ? `${history.battery.pct}%` : DASH },
        { label: 'Power', value: { mains: 'Mains', battery: 'On battery' }[history.power?.state] ?? DASH },
      ],
      note: 'In sim mode the hub sends these, a beat every 5 s.',
    },
    {
      id: 'presence', name: 'Presence', role: 'From the camera service or sim keys',
      status: beat('presence', seen.presence),
      facts: [
        { label: 'Last update', value: ago(seen.presence, now) },
        { label: 'Last state', value: PRESENCE_WORD[history.presence?.state] ?? DASH },
      ],
      note: 'The camera service repeats its state every 5 s. Sim keys send only on change.',
    },
    {
      id: 'camera', name: 'Help sign', role: 'From the camera service or sim keys',
      status: heard(seen.camera),
      facts: [{ label: 'Last message', value: ago(seen.camera, now) }],
      note: 'Sends only when the sign is seen, so quiet is normal.',
    },
    {
      id: 'agent', name: 'Agent', role: 'Plans each step and runs the alarm rule',
      status: heard(seen.agent),
      facts: [{ label: 'Last message', value: ago(seen.agent, now) }],
      note: QUIET_IS_NORMAL,
    },
    {
      id: 'voice', name: 'Voice', role: 'Speaks the prompt and hears the reply',
      status: heard(seen.voice),
      facts: [{ label: 'Last message', value: ago(seen.voice, now) }],
      note: QUIET_IS_NORMAL,
    },
  ];

  return { eyebrow: 'Hub and services', title: 'System', detail: headDetail(parts, ctx), parts };
}

function headDetail(parts, ctx) {
  const off = offlineLine(ctx);
  if (off) return ctx.linkAt == null ? off : `${off}. Times below are last known`;
  const status = (id) => parts.find((p) => p.id === id).status;
  if (status('sensors') === STALE.sensors) return 'Hub connected. Box sensors not reporting';
  const live = parts.filter((p) => p.status === REPORTING).map((p) => p.name.toLowerCase());
  if (live.length) return `Hub connected. ${sentence(joinAnd(live))} reporting`;
  return 'Hub connected. No heartbeat yet';
}

const PART_ICONS = {
  hub: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="2.5"/><circle cx="4" cy="5" r="1.8"/><circle cx="20" cy="5" r="1.8"/><circle cx="4" cy="19" r="1.8"/><circle cx="20" cy="19" r="1.8"/><path d="M5.4 6.3 10 10.4M18.6 6.3 14 10.4M5.4 17.7 10 13.6M18.6 17.7 14 13.6"/></svg>',
  sensors: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg>',
  presence: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="6" r="2.5"/><path d="M12 9v6M8 12h8M12 15l-3 6M12 15l3 6"/></svg>',
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="3.5"/></svg>',
  agent: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/><path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01" stroke-linecap="round" stroke-width="2.4"/></svg>',
  voice: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
};

function partCard(p) {
  return h('section', { class: 'card part', 'data-part': p.id },
    cardHead(PART_ICONS[p.id], p.name, p.role, tag(p.status.text, p.status.tone)),
    h('dl', { class: 'facts' }, p.facts.map((f) => h('div', {}, h('dt', {}, f.label), h('dd', {}, f.value)))),
    h('p', { class: 'card-note' }, p.note));
}

export function renderSystem(root, history, ctx) {
  const m = systemModel(history, ctx);
  root.replaceChildren(
    screenHead(m.eyebrow, m.title, m.detail),
    h('div', { class: 'parts' }, m.parts.map(partCard)));
}
