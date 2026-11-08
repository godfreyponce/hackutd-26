import { initialState, reduce, statusText, questionOpen, tryAnswered, activeAlert, alertChip, TRACE_WINDOW_MS, initialHistory, record, tryText, heardChip } from './state.js';
import { HOME_COUNT } from '../dashboard/homes.js';
import { renderAlerts } from './views/alerts.js';
import { renderDisasters } from './views/disasters.js';
import { renderSecurity } from './views/security.js';
import { renderSystem } from './views/system.js';

// The product name is not settled. Change it here only.
export const PRODUCT_NAME = 'LAND';

const DEFAULT_HUB = 'ws://localhost:8765';
const RETRY_MS = 1000; // guess: fast enough to catch a hub restart during the demo
const HOME = { x: 150, y: 130 };

const hubUrl = new URLSearchParams(location.search).get('hub') || DEFAULT_HUB;
const $ = (id) => document.getElementById(id);

let state = initialState();
let history = initialHistory();
let connected = false;
let linkAt = null; // when the hub link last opened or closed
let shownAlert = null;
let lastWaveAt = null;

document.title = `${PRODUCT_NAME} Home`;
$('hub').title = `Hub ${hubUrl}`;

// ---------- neighborhood map (tactical display) ----------

// Roof centers read off the map/ tiles in view units, off streets and bare canopy, so each dot sits on a house.
const ROOFS = [
  [122, -84], [33, -83], [183, -82], [236, -82], [33, -57], [208, -57], [88, -56], [275, -55],
  [112, -37], [48, -35], [156, -33], [242, -33], [268, -20], [103, -15], [182, -8], [225, -7], [32, -5],
  [156, 23], [65, 28], [117, 42], [213, 47], [270, 47], [46, 65], [122, 73], [198, 73], [272, 73],
  [14, 75], [36, 87], [95, 97], [167, 97], [45, 123], [288, 124], [195, 125], [47, 137], [75, 138],
  [122, 140], [212, 150], [258, 150], [167, 177], [238, 177], [125, 183], [197, 200], [275, 201], [68, 206],
  [38, 223], [133, 228], [182, 228], [258, 228], [22, 263], [117, 278], [213, 280], [157, 283], [65, 285],
  [77, 302], [227, 302], [25, 332], [108, 332], [215, 333], [275, 334],
];

const SVG = 'http://www.w3.org/2000/svg';
function svgEl(tag, attrs, parent) {
  const el = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (parent) parent.append(el);
  return el;
}
function hudText(parent, x, y, text, attrs = {}) {
  const el = svgEl('text', { x, y, class: 'hud', ...attrs }, parent);
  el.textContent = text;
  return el;
}

const map = $('map');
map.innerHTML = `
  <defs>
    <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="1.6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="sweep-fill" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#bfe0ff" stop-opacity="0"/>
      <stop offset="1" stop-color="#bfe0ff" stop-opacity="0.16"/>
    </linearGradient>
    <radialGradient id="vignette" cx="50%" cy="50%" r="65%">
      <stop offset="0.6" stop-color="#030a16" stop-opacity="0"/>
      <stop offset="1" stop-color="#030a16" stop-opacity="0.5"/>
    </radialGradient>
    <clipPath id="scope"><circle cx="${HOME.x}" cy="${HOME.y}" r="124"/></clipPath>
  </defs>`;

// USGS The National Map imagery of Richardson, TX (USGSImageryOnly, public domain), saved in map/ so the page works offline.
// Zoom 16 is the closest zoom the service has here: one view unit is one imagery pixel, about 2 m, so the outer
// ring spans about 500 m. Offsets put lat 32.9433, lon -96.7215, a block of houses with yards and trees, on HOME.
const TILE = 256;
const IMAGERY = { x0: -204, y0: -174, x1: -204 + 3 * TILE, y1: -174 + 3 * TILE };
for (const [col, x] of [[0, 15159], [1, 15160], [2, 15161]]) {
  for (const [row, y] of [[0, 26409], [1, 26410], [2, 26411]]) {
    svgEl('image', { href: `map/16-${x}-${y}.jpg`, x: IMAGERY.x0 + col * TILE, y: IMAGERY.y0 + row * TILE, width: TILE, height: TILE }, map);
  }
}
const vignette = svgEl('rect', { width: 300, height: 260, fill: 'url(#vignette)' }, map);

const scope = svgEl('g', {}, map);
for (const r of [40, 82, 124]) svgEl('circle', { cx: HOME.x, cy: HOME.y, r, class: 'range' }, scope);
// One view unit is about 2 m, so the rings sit at about 80, 160 and 250 m. The 80 m ring is left unlabeled:
// its label would crowd the reticle. The others sit at their ring's south-east point, clear of the N tick,
// THIS HOME and the corner counts.
const ringLabels = [[82, '160 m'], [124, '250 m']].map(([r, text]) =>
  hudText(scope, HOME.x + r * 0.71 + 3, HOME.y + r * 0.71 + 10, text, { class: 'hud dim' }));
svgEl('path', { d: `M${HOME.x - 124} ${HOME.y}H${HOME.x + 124}M${HOME.x} ${HOME.y - 124}V${HOME.y + 124}`, class: 'cross' }, scope);
for (let deg = 0; deg < 360; deg += 10) {
  const a = (deg * Math.PI) / 180;
  const inner = deg % 30 === 0 ? 116 : 120;
  svgEl('line', {
    x1: HOME.x + Math.sin(a) * inner, y1: HOME.y - Math.cos(a) * inner,
    x2: HOME.x + Math.sin(a) * 124, y2: HOME.y - Math.cos(a) * 124, class: deg === 0 ? 'tick north' : 'tick',
  }, scope);
}
const hudNorth = hudText(scope, HOME.x + 7, HOME.y - 106, 'N');

const sweepGroup = svgEl('g', { 'clip-path': 'url(#scope)' }, map);
const sweep = svgEl('g', { class: 'sweep' }, sweepGroup);
svgEl('path', { d: `M${HOME.x} ${HOME.y}L${HOME.x + 124} ${HOME.y}A124 124 0 0 0 ${HOME.x + 124 * Math.cos(-0.7)} ${HOME.y + 124 * Math.sin(-0.7)}Z`, fill: 'url(#sweep-fill)' }, sweep);
svgEl('line', { x1: HOME.x, y1: HOME.y, x2: HOME.x + 124, y2: HOME.y, class: 'sweep-edge' }, sweep);

const wave = svgEl('circle', { class: 'wave', cx: HOME.x, cy: HOME.y, r: 4 }, map);
// A hidden Overview restarts its animations when shown, so a finished wave must not keep `go` and replay.
wave.addEventListener('animationend', () => wave.classList.remove('go'));

const neighborDots = ROOFS.map(([x, y]) => {
  const el = svgEl('circle', { class: 'node', cx: x, cy: y, r: 3.6, filter: 'url(#glow)' }, map);
  el.style.transitionDelay = `${Math.round(Math.hypot(x - HOME.x, y - HOME.y) * 6)}ms`;
  return el;
});

// Reticle on this home: four corner brackets.
const b = 15, l = 5;
svgEl('path', {
  class: 'reticle',
  d: [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) =>
    `M${HOME.x + sx * b} ${HOME.y + sy * (b - l)}V${HOME.y + sy * b}H${HOME.x + sx * (b - l)}`).join(''),
}, map);
// This home is the real box: a blue ring, as on the operator dashboard, and a red ring inside it while help is contacted.
svgEl('circle', { class: 'ring escalated', cx: HOME.x, cy: HOME.y, r: 8 }, map);
svgEl('circle', { class: 'ring real', cx: HOME.x, cy: HOME.y, r: 11 }, map);
const homeDot = svgEl('circle', { class: 'node home', cx: HOME.x, cy: HOME.y, r: 4.5, filter: 'url(#glow)' }, map);
const homeLabelBg = svgEl('rect', { class: 'hud-bg', rx: 2 }, map);
const hudThisHome = hudText(map, 0, 0, 'THIS HOME', { 'text-anchor': 'middle' });

const hudNodes = hudText(map, 6, 254, '');
const hudHit = hudText(map, 294, 254, '', { 'text-anchor': 'end' });
const hudEscalated = hudText(map, 294, 254, 'ESCALATED 1', { 'text-anchor': 'end', class: 'hud alarm' });
const hudGrid = hudText(map, 6, 14, 'RICHARDSON, TX');
const hudLive = hudText(map, 294, 14, '', { 'text-anchor': 'end' });
const backing = (el) => {
  const bg = svgEl('rect', { class: 'hud-bg', rx: 2 });
  el.before(bg);
  return bg;
};
const corners = [[hudGrid, false, false], [hudLive, true, false], [hudNodes, false, true], [hudHit, true, true]]
  .map(([el, right, bottom]) => ({ el, bg: backing(el), right, bottom }));
const northBg = backing(hudNorth);
const escalatedBg = backing(hudEscalated);
const ringLabelBgs = ringLabels.map(backing);

const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

// Grow the 300x260 scope view to the card's shape so the imagery fills it with no letterbox,
// centered on this home but kept inside the imagery so no black strip shows past the tiles.
function fitMap() {
  const { width, height } = map.getBoundingClientRect();
  if (!width || !height) return;
  const k = Math.max(300 / width, 260 / height);
  const w = width * k, h = height * k;
  const x = clamp(HOME.x - w / 2, IMAGERY.x0, IMAGERY.x1 - w), y = clamp(HOME.y - h / 2, IMAGERY.y0, IMAGERY.y1 - h);
  map.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
  for (const [k2, v] of Object.entries({ x, y, width: w, height: h })) vignette.setAttribute(k2, v);
  // HUD text is 1u on screen, never under 18 px so it reads from 2 m at 1280x800.
  const f = Math.max(18, parseFloat(getComputedStyle(document.body).fontSize)) * k;
  map.style.setProperty('--hud', `${f}px`);
  // Just under the reticle's lower brackets, so it never covers the rings at this home's center.
  hudThisHome.setAttribute('x', HOME.x);
  hudThisHome.setAttribute('y', HOME.y + b + 3 + 0.8 * f);
  view = { x, y, w, h, f };
  placeHud();
}

let view = { x: 0, y: 0, w: 300, h: 260, f: 11 };
const HUD_PAD = 4;
const DOT_CLEAR = 3.6 + 2.5; // a dot's radius plus room for its outline, kept between its center and any HUD backing box
const DOT_EXTENT = 5; // a dot's radius plus its outline and glow, in view units
function fitBacking(bg, ...els) {
  const boxes = els.map((el) => el.getBBox());
  const x0 = Math.min(...boxes.map((bb) => bb.x)), y0 = Math.min(...boxes.map((bb) => bb.y));
  const x1 = Math.max(...boxes.map((bb) => bb.x + bb.width)), y1 = Math.max(...boxes.map((bb) => bb.y + bb.height));
  const box = { x: x0 - HUD_PAD, y: y0, width: x1 - x0 + 2 * HUD_PAD, height: y1 - y0 };
  for (const [k, v] of Object.entries(box)) bg.setAttribute(k, v);
  return box;
}
// Called again after the corner texts change, since each backing box is sized to its text.
// A dot under a backing box is hidden, so no dot sits under or touches the HUD text.
function placeHud() {
  const { x, y, w, h, f } = view;
  const boxes = [fitBacking(homeLabelBg, hudThisHome), fitBacking(northBg, hudNorth),
    ...ringLabels.map((el, i) => fitBacking(ringLabelBgs[i], el))];
  for (const corner of corners) {
    const { el, bg, right, bottom } = corner;
    el.setAttribute('x', right ? x + w - 2 * HUD_PAD : x + 2 * HUD_PAD);
    el.setAttribute('y', bottom ? y + h - HUD_PAD - 0.45 * f : y + HUD_PAD + 1.05 * f);
    corner.box = fitBacking(bg, el);
    boxes.push(corner.box);
  }
  // While help is contacted the escalation sits directly above the hit count, so both stay readable.
  // It is placed in every state, so the same dots stay hidden when it shows or hides.
  const hitCorner = corners.find((c) => c.el === hudHit);
  hudEscalated.setAttribute('x', x + w - 2 * HUD_PAD);
  hudEscalated.setAttribute('y', Number(hudHit.getAttribute('y')) - hitCorner.box.height - HUD_PAD);
  const escBox = fitBacking(escalatedBg, hudEscalated);
  // The two chips are one stack: the same width and the same edges.
  const left = Math.min(escBox.x, hitCorner.box.x);
  const width = Math.max(escBox.x + escBox.width, hitCorner.box.x + hitCorner.box.width) - left;
  escalatedBg.setAttribute('x', left);
  escalatedBg.setAttribute('width', width);
  const escalated = hudEscalated.style.visibility !== 'hidden';
  escalatedBg.style.visibility = escalated ? '' : 'hidden';
  if (escalated) {
    hitCorner.bg.setAttribute('x', left);
    hitCorner.bg.setAttribute('width', width);
  }
  boxes.push({ ...escBox, x: left, width }, { ...hitCorner.box, x: left, width });
  for (const dot of neighborDots) {
    const cx = dot.cx.baseVal.value, cy = dot.cy.baseVal.value;
    const covered = boxes.some((bb) => cx > bb.x - DOT_CLEAR && cx < bb.x + bb.width + DOT_CLEAR
      && cy > bb.y - DOT_CLEAR && cy < bb.y + bb.height + DOT_CLEAR);
    // A dot cut by the map's edge reads as a glitch, so it is hidden too.
    const cut = cy < y + DOT_EXTENT || cy > y + h - DOT_EXTENT || cx < x + DOT_EXTENT || cx > x + w - DOT_EXTENT;
    dot.style.visibility = covered || cut ? 'hidden' : '';
  }
}
new ResizeObserver(fitMap).observe(map);

function renderMap() {
  for (const el of neighborDots) el.classList.toggle('hit', state.areaHit);
  homeDot.classList.toggle('hit', state.home === 'hit');
  homeDot.classList.toggle('ok', state.home === 'ok');
  const last = state.quakes.at(-1)?.at ?? null;
  if (last !== null && last !== lastWaveAt) {
    wave.classList.remove('go');
    void wave.getBoundingClientRect();
    wave.classList.add('go');
  }
  lastWaveAt = last;
  const total = neighborDots.length + 1;
  // A home that answered okay was still hit, so check-in answers never lower the quake count.
  const hit = state.areaHit ? neighborDots.length + (state.home === 'idle' ? 0 : 1) : state.home === 'hit' ? 1 : 0;
  hudNodes.textContent = `NEARBY ${total} OF ${HOME_COUNT}`;
  const escalated = connected && state.status === 'CONTACTING_HELP';
  hudHit.textContent = connected ? `HIT ${hit}` : 'HIT --';
  // Red only while an event is unresolved; a protected home that was hit reads neutral, like NEARBY. The dots keep their encoding.
  hudHit.classList.toggle('alarm', connected && hit > 0 && state.status !== 'PROTECTED');
  hudHit.classList.toggle('warn', !connected);
  hudEscalated.style.visibility = escalated ? '' : 'hidden';
  hudLive.textContent = connected ? 'DEMO' : 'NO LINK';
  hudLive.classList.toggle('warn', !connected);
  $('legend-not-hit').textContent = connected ? 'Not hit' : 'Unknown';
  placeHud();
  const homeNote = { hit: 'This home was hit', ok: 'This home is okay', idle: '' }[state.home];
  // One line in every state, so the map below never moves when the text changes.
  $('map-sub').textContent = !connected ? 'No live data'
    : `Simulated neighbors. ${state.areaHit ? (hit === total ? `Quake hit all ${total}.` : `Quake hit ${hit} of ${total}.`) : homeNote ? `${homeNote}.` : 'All quiet.'}`;
}

// ---------- seismic trace ----------

const canvas = $('trace');
const ctx = canvas.getContext('2d');

let labelPx = 12;
let unitPx = 12;
function sizeCanvas() {
  const r = canvas.getBoundingClientRect();
  unitPx = parseFloat(getComputedStyle(document.body).fontSize);
  labelPx = Math.max(18, unitPx);
  canvas.width = Math.max(1, Math.round(r.width * devicePixelRatio));
  canvas.height = Math.max(1, Math.round(r.height * devicePixelRatio));
}
new ResizeObserver(sizeCanvas).observe(canvas);

const RING_S = 10; // how long one quake's wiggle lasts on the trace

// Each quake event carries only its peak, so the trace draws a damped wiggle that peaks at that value.
function signal(t) {
  let g = 0;
  for (const q of state.quakes) {
    const dt = (t - q.at) / 1000;
    // The decay scales with RING_S, so the wiggle fades to about 0.1% of its peak by the end of the ring.
    if (dt >= 0 && dt < RING_S) g += q.g * Math.exp((-dt * 6.6) / RING_S) * Math.cos(dt * 2 * Math.PI * 0.4);
  }
  return g;
}

function drawTrace() {
  const now = Date.now();
  const { width: w, height: h } = canvas;
  const dpr = devicePixelRatio;
  ctx.clearRect(0, 0, w, h);
  const maxG = Math.max(1, ...state.quakes.map((q) => q.g)) * 1.15;
  const fs = labelPx * dpr;
  const plotH = h - fs * 1.4; // the bottom band holds only the time labels
  const mid = plotH / 2;
  const scale = (plotH / 2 - fs * 0.6) / maxG;
  ctx.font = `${fs}px system-ui, sans-serif`;
  const gutter = ctx.measureText('+1 g').width + 10 * dpr;
  // The trace and "now" stop short of the card's right edge.
  const plotW = w - unitPx * 1.5 * dpr - gutter;

  ctx.globalAlpha = connected ? 1 : 0.35;
  ctx.strokeStyle = 'rgba(120,170,235,0.18)';
  ctx.lineWidth = dpr;
  ctx.beginPath();
  for (const g of [-1, 1]) { ctx.moveTo(gutter, mid - g * scale); ctx.lineTo(w, mid - g * scale); }
  ctx.stroke();
  // Offline only the faded grid stays, with the "No live signal" text in the middle.
  if (connected) {
    ctx.fillStyle = 'rgba(143,166,198,0.9)';
    ctx.textBaseline = 'middle';
    ctx.fillText('+1 g', 4 * dpr, mid - scale);
    ctx.fillText('-1 g', 4 * dpr, mid + scale);
    ctx.fillText('0 g', 4 * dpr, mid);
    ctx.save();
    ctx.strokeStyle = 'rgba(120,170,235,0.25)';
    ctx.setLineDash([2 * dpr, 4 * dpr]);
    ctx.beginPath();
    ctx.moveTo(gutter, mid);
    ctx.lineTo(w, mid);
    ctx.stroke();
    ctx.restore();
    ctx.textBaseline = 'alphabetic';
    ctx.fillText('60 s ago', gutter, h - fs * 0.3);
    ctx.textAlign = 'right';
    ctx.fillText('now', gutter + plotW, h - fs * 0.3);
    ctx.textAlign = 'left';
  }
  ctx.globalAlpha = 1;

  // Offline there is no live signal, so draw no line rather than a flat one that reads as calm.
  if (!connected) {
    ctx.font = `${Math.max(22, labelPx * 1.25) * dpr}px system-ui, sans-serif`;
    ctx.fillStyle = '#8fa6c6';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('No live signal', gutter + plotW / 2, mid);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    requestAnimationFrame(drawTrace);
    return;
  }
  const steps = Math.min(w, 1200);
  // Samples sit on a fixed time grid, so they do not slide between frames and the burst does not shimmer.
  const stepMs = TRACE_WINDOW_MS / steps;
  const start = Math.floor((now - TRACE_WINDOW_MS) / stepMs) * stepMs;
  const trace = new Path2D();
  for (let i = 0; i <= steps; i++) {
    const x = gutter + (i / steps) * plotW;
    const y = mid - signal(start + (i / steps) * TRACE_WINDOW_MS) * scale;
    i ? trace.lineTo(x, y) : trace.moveTo(x, y);
  }
  ctx.lineWidth = 2 * dpr;
  ctx.strokeStyle = 'rgba(77,163,255,0.7)';
  ctx.stroke(trace);
  // Only the shaking itself turns red, so the eye goes to the event.
  ctx.strokeStyle = '#ff5a4e';
  for (const q of state.quakes) {
    const qx = gutter + ((q.at - start) / TRACE_WINDOW_MS) * plotW;
    // The samples can miss the exact peak, so the onset draws it, matching the peak value in the card head.
    if (q.at >= start) {
      ctx.beginPath();
      ctx.moveTo(qx, mid);
      ctx.lineTo(qx, mid - q.g * scale);
      ctx.stroke();
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(qx, 0, ((RING_S * 1000) / TRACE_WINDOW_MS) * plotW, h);
    ctx.clip();
    ctx.stroke(trace);
    ctx.restore();
  }
  requestAnimationFrame(drawTrace);
}
requestAnimationFrame(drawTrace);

function renderQuake() {
  const recent = state.quakes.filter((q) => Date.now() - q.at <= TRACE_WINDOW_MS);
  const last = recent.at(-1);
  const peak = document.createElement('small');
  peak.textContent = 'peak';
  $('quake-peak').replaceChildren(...(last ? [`${last.g.toFixed(2)} g`, peak] : []));
  $('quake-sub').textContent = !connected ? 'Live seismic data unavailable' : last ? `${recent.length} event${recent.length > 1 ? 's' : ''} in the last minute` : 'No shaking in the last minute';
}

// ---------- the rest ----------

const timeOf = (at) => new Date(at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

function render() {
  const a = activeAlert(state, Date.now());
  shownAlert = a;
  const { word, detail, note } = statusText(state.status, { alert: Boolean(a), linked: connected, helpSign: state.helpSign, ended: state.ended, questionOpen: questionOpen(state), tryNum: state.tryNum, answered: tryAnswered(state) });
  document.body.dataset.status = state.status;
  document.body.dataset.link = connected ? 'up' : 'down';
  $('word').textContent = word;
  $('detail').textContent = detail;
  $('note').hidden = !note;
  $('note').textContent = note ?? '\u00a0'; // one blank line keeps the hidden note's height

  $('say').textContent = state.say ? `"${state.say.text}"` : connected ? 'No prompt yet' : 'Prompt unavailable';
  $('say-try').textContent = tryText(state.say?.tryNum);
  const heard = state.heard;
  $('heard').textContent = heard ? (heard.transcript ? `"${heard.transcript}"` : '') : connected ? 'No reply yet' : 'Reply unavailable';
  $('heard-chip').hidden = !heard;
  $('heard-chip').className = `chip ${heard?.answer ?? ''}`;
  $('heard-chip').textContent = heardChip(heard, state.status);

  $('banner').hidden = !a;
  $('alert-count').hidden = !a;
  if (a) {
    $('banner').dataset.level = a.level;
    $('alert-source').textContent = alertChip(a);
    $('alert-event').textContent = a.event;
    $('alert-headline').textContent = a.headline;
    // The headline often names the area already; then the space shows when the alert came in.
    $('alert-area').textContent = a.headline.includes(a.area)
      ? `Received ${timeOf(a.at)}` : a.area;
  }

  $('battery').hidden = !state.onBattery;
  $('battery-text').textContent = state.batteryPct == null ? 'On battery' : `On battery, ${state.batteryPct}%`;

  $('scale-mark').hidden = !connected || state.indoorF == null;
  if (state.indoorF != null) $('scale-mark').style.setProperty('--at', clamp((state.indoorF - 50) / 50, 0, 1));
  // With no reading the gauge still shows an empty value at full size, so the card keeps its shape.
  // The dash stands alone: a dash before the unit reads as a negative temperature.
  $('temp').innerHTML = state.indoorF == null ? '<span class="no-reading">\u2013</span>' : `${Math.round(state.indoorF)}<small> &deg;F</small>`;
  // Only the box's own sensor sends a real reading. Without one the value is the dashboard's fixed H000 profile.
  const simulatedHeat = state.indoorF != null && !state.indoorLive;
  $('heat-kind').textContent = simulatedHeat ? 'Indoor temperature, simulated' : 'Indoor temperature';
  $('heat-msg').textContent = !connected ? `${state.indoorF == null ? '' : 'Last known reading. '}No live heat data`
    : a && /heat/i.test(a.event) ? `${a.source}: ${a.event}` : state.indoorF == null ? 'No reading yet' : simulatedHeat ? 'Simulated reading' : 'No heat alerts';
  $('heat-at').hidden = state.indoorAt == null || simulatedHeat;
  $('heat-at').textContent = state.indoorAt == null ? '' : `Updated ${timeOf(state.indoorAt)}`;

  $('hub').classList.toggle('bad', !connected);
  $('hub-text').textContent = connected ? 'Hub connected' : 'Hub offline, retrying';

  renderQuake();
  renderMap();
  renderScreen();
}

// ---------- side screens (#52): hash routes on one page, so the history and the hub link survive a switch ----------

const SCREENS = { alerts: renderAlerts, disasters: renderDisasters, security: renderSecurity, system: renderSystem };
const route = () => {
  const name = location.hash.slice(1);
  return Object.hasOwn(SCREENS, name) ? name : 'overview';
};

// The fade under a list says there is more below, so it goes once the list is scrolled to its end.
const clip = (el) => el.classList.toggle('clipped', el.scrollTop + el.clientHeight < el.scrollHeight - 1);
// A list can come or go between renders, so its scroll is kept by its card's title, not its place.
const listKey = (el) => el.closest('.card')?.querySelector('.card-title')?.textContent;
// What each screen's view last drew. root.innerHTML also carries the `clipped` marks, so it cannot be compared.
const drawn = {};

function renderScreen() {
  const name = route();
  if (name === 'overview') return;
  const root = $(`screen-${name}`);
  const now = Date.now();
  const next = document.createElement('section');
  SCREENS[name](next, history, { now, connected, linkAt, alert: activeAlert(state, now) });
  // Swap only on a change, so a touch scroll or a text selection lives through the clock tick.
  if (next.innerHTML !== drawn[name]) {
    drawn[name] = next.innerHTML;
    const scrolls = new Map([...root.querySelectorAll('.log')].map((el) => [listKey(el), el.scrollTop]));
    root.replaceChildren(...next.childNodes);
    for (const el of root.querySelectorAll('.log')) el.scrollTop = scrolls.get(listKey(el)) ?? 0;
  }
  for (const el of root.querySelectorAll('.log')) clip(el);
}
for (const screen of document.querySelectorAll('.screen')) {
  screen.addEventListener('scroll', (e) => { if (e.target.classList?.contains('log')) clip(e.target); }, true);
}

function showRoute() {
  const name = route();
  document.querySelector('main').hidden = name !== 'overview';
  for (const el of document.querySelectorAll('.screen')) el.hidden = el.dataset.screen !== name;
  for (const a of document.querySelectorAll('nav a')) {
    const on = a.dataset.screen === name;
    a.classList.toggle('active', on);
    if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  }
  renderScreen();
}
addEventListener('hashchange', showRoute);

function connect() {
  const ws = new WebSocket(hubUrl);
  ws.onopen = () => { connected = true; linkAt = Date.now(); render(); };
  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    const now = Date.now();
    state = reduce(state, msg, now);
    history = record(history, msg, now);
    render();
  };
  ws.onclose = () => {
    // Every failed retry closes again; the time stays at when the link was lost. A hub never reached keeps null.
    if (connected) linkAt = Date.now();
    connected = false;
    render();
    setTimeout(connect, RETRY_MS);
  };
}

function tick() {
  $('clock').textContent = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  renderQuake();
  if (activeAlert(state, Date.now()) !== shownAlert) render();
  else renderScreen(); // ages and live or stale states move with the clock
}
setInterval(tick, 1000);
tick();
render();
showRoute();
connect();
