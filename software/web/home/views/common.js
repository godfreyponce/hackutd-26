// Small DOM and wording helpers shared by the side screens. Pure helpers first, so node tests can import this file.

export const DASH = '--';

// One form for a distance on every screen: tenths under 10 mi, whole miles past that.
export const miles = (d) => `${d < 10 ? +d.toFixed(1) : Math.round(d)} mi away`;

export const clockTime = (at) => new Date(at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', second: '2-digit' });

export function ago(at, now) {
  if (at == null) return DASH;
  const s = Math.floor((now - at) / 1000);
  if (s < 1) return 'just now';
  if (s < 60) return `${s} s ago`;
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  return `${Math.floor(s / 3600)} h ago`;
}

// The head line while the hub link is down, in one form on every screen, or null while it is up.
// linkAt is null until the link first opens, so a hub never reached claims no last known data.
export function offlineLine(ctx, lastKnown) {
  if (ctx.connected) return null;
  if (ctx.linkAt == null) return 'Hub offline. Nothing received yet';
  if (!lastKnown) return 'Hub offline';
  // "Someone is still" reads mid-sentence as "someone is still"; "USGS" keeps its capitals.
  const phrase = /^[A-Z][a-z]/.test(lastKnown) ? lastKnown[0].toLowerCase() + lastKnown.slice(1) : lastKnown;
  return `Hub offline. Last known: ${phrase}`;
}

// h('li', { class: 'x', title: 'y' }, 'text', child): an element with attributes and children. Strings become text.
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null && v !== false) el.setAttribute(k, v === true ? '' : v);
  el.append(...children.flat().filter((c) => c != null && c !== false));
  return el;
}

export const time = (at) => h('time', { datetime: new Date(at).toISOString() }, clockTime(at));

export const tag = (text, cls = '') => h('span', { class: `tag ${cls}`.trim() }, text);

// A count in a card head, like Overview's value with a small unit: "3 events".
export const count = (n, unit) => h('span', {}, String(n), h('small', {}, unit));

// One list row, the same on every screen: the time, a label, a muted line under it, a wide line under that
// (a headline or a quote), and at the right a tag with a small state under it. An active row takes the tint
// of its level, like the Overview banner.
export function logRow({ at, what, more, wide, tag: t, state, level, active }) {
  return h('li', { class: active ? 'active' : null, 'data-level': level },
    time(at),
    h('div', { class: 'what' }, what),
    t || state ? h('div', { class: 'side' }, t ? tag(t.text, t.cls) : null, state ? h('span', { class: 'state' }, state) : null) : null,
    more ? h('div', { class: 'more' }, more) : null,
    wide ? h('div', { class: 'wide' }, wide) : null);
}

// The eyebrow, title and line under it, like the Overview hero's "Home status" over its status word.
export function screenHead(eyebrow, title, detail) {
  return h('div', { class: 'screen-head' },
    h('div', { class: 'eyebrow' }, eyebrow),
    h('div', { class: 'screen-title' }, title),
    h('div', { class: 'screen-detail' }, detail));
}

// The card head from Overview: an icon, a title, a line under it, and an optional value at the right.
export function cardHead(iconSvg, title, sub, value) {
  const icon = h('span', { 'aria-hidden': 'true', style: 'display: contents' });
  icon.innerHTML = iconSvg;
  return h('div', { class: 'card-head' }, icon,
    h('div', {}, h('div', { class: 'card-title' }, title), sub == null ? null : h('div', { class: 'card-sub' }, sub)),
    value == null ? null : h('div', { class: value.classList?.contains('tag') ? 'card-tag' : 'card-value' }, value));
}

export const empty = (text, sub) => h('div', { class: 'empty' }, h('span', {}, text), sub ? h('small', {}, sub) : null);

// The same icons as the nav, so a screen's cards match its nav entry.
export const ICONS = {
  alert: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3 2 21h20L12 3z"/><path d="M12 10v5M12 18v.5"/></svg>',
  wave: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2 12h4l2-5 3 10 3-14 3 13 2-4h3"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/></svg>',
  gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/></svg>',
  chat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg>',
};
