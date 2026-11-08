import { initialState, reduce, statusText, TRACE_WINDOW_MS } from './state.js';

// The product name is not settled. Change it here only.
export const PRODUCT_NAME = 'LAND';

const DEFAULT_HUB = 'ws://localhost:8765';
const RETRY_MS = 1000; // guess: fast enough to catch a hub restart during the demo
const HOME = { x: 150, y: 130 };

const hubUrl = new URLSearchParams(location.search).get('hub') || DEFAULT_HUB;
const $ = (id) => document.getElementById(id);

let state = initialState();
let connected = false;
let lastWaveAt = null;

document.title = `${PRODUCT_NAME} Home`;
$('product-name').textContent = PRODUCT_NAME;
$('hub').title = `Hub ${hubUrl}`;

// ---------- neighborhood map (tactical display) ----------

function neighbors() {
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const dots = [];
  // Rows run from about 190 units above this home to 190 below, so the dots fill the tall map view.
  for (let row = -2; row < 8; row++) {
    for (let col = 0; col < 7; col++) {
      const x = 22 + col * 43 + (rand() - 0.5) * 22;
      const y = 22 + row * 42 + (rand() - 0.5) * 22;
      // Keep clear of this home and of its H000 labels on its left.
      const clear = Math.hypot(x - HOME.x, y - HOME.y) > 24 && !(x < HOME.x && Math.abs(y - HOME.y) < 26);
      if (clear && rand() > 0.2) dots.push({ x, y });
    }
  }
  return dots;
}

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

const neighborDots = neighbors().map(({ x, y }) => {
  const el = svgEl('circle', { class: 'node', cx: x, cy: y, r: 3, filter: 'url(#glow)' }, map);
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
const homeLabelBg = svgEl('rect', { class: 'hud-bg' }, map);
const hudHome = hudText(map, 0, 0, 'H000', { 'text-anchor': 'end' });
const hudThisHome = hudText(map, 0, 0, 'THIS HOME', { class: 'hud dim', 'text-anchor': 'end' });

const hudNodes = hudText(map, 6, 254, '');
const hudHit = hudText(map, 294, 254, '', { 'text-anchor': 'end' });
const hudGrid = hudText(map, 6, 14, 'RICHARDSON, TX');
const hudLive = hudText(map, 294, 14, '', { 'text-anchor': 'end' });
const backing = (el) => {
  const bg = svgEl('rect', { class: 'hud-bg' });
  el.before(bg);
  return bg;
};
const corners = [[hudGrid, false, false], [hudLive, true, false], [hudNodes, false, true], [hudHit, true, true]]
  .map(([el, right, bottom]) => ({ el, bg: backing(el), right, bottom }));
const northBg = backing(hudNorth);

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
  for (const el of [hudHome, hudThisHome]) el.setAttribute('x', HOME.x - b - 0.6 * f);
  hudHome.setAttribute('y', HOME.y - 0.36 * f);
  hudThisHome.setAttribute('y', HOME.y + 0.82 * f);
  view = { x, y, w, h, f };
  placeHud();
}

let view = { x: 0, y: 0, w: 300, h: 260, f: 11 };
const HUD_PAD = 4;
const DOT_CLEAR = 6; // view units kept between a dot's center and any HUD backing box
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
  const boxes = [fitBacking(homeLabelBg, hudHome, hudThisHome), fitBacking(northBg, hudNorth)];
  for (const { el, bg, right, bottom } of corners) {
    el.setAttribute('x', right ? x + w - 2 * HUD_PAD : x + 2 * HUD_PAD);
    el.setAttribute('y', bottom ? y + h - HUD_PAD - 0.45 * f : y + HUD_PAD + 1.05 * f);
    boxes.push(fitBacking(bg, el));
  }
  for (const dot of neighborDots) {
    const cx = dot.cx.baseVal.value, cy = dot.cy.baseVal.value;
    const covered = boxes.some((bb) => cx > bb.x - DOT_CLEAR && cx < bb.x + bb.width + DOT_CLEAR
      && cy > bb.y - DOT_CLEAR && cy < bb.y + bb.height + DOT_CLEAR);
    dot.style.visibility = covered ? 'hidden' : '';
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
  hudNodes.textContent = `NODES ${total}`;
  hudHit.textContent = connected ? `HIT ${hit}` : 'HIT --';
  hudHit.classList.toggle('alarm', connected && hit > 0);
  hudHit.classList.toggle('warn', !connected);
  hudLive.textContent = connected ? 'LIVE' : 'NO LINK';
  hudLive.classList.toggle('warn', !connected);
  $('legend-not-hit').textContent = connected ? 'Not hit' : 'Unknown';
  placeHud();
  const homeNote = { hit: 'This home was hit', ok: 'This home is okay', idle: '' }[state.home];
  $('map-sub').textContent = !connected ? 'No live data'
    : state.areaHit ? `Quake hit ${hit} of ${total} homes${state.home === 'ok' ? '. This home answered okay' : ''}` : homeNote ? `${homeNote}.` : 'All homes quiet';
}

// ---------- seismic trace ----------

const canvas = $('trace');
const ctx = canvas.getContext('2d');

let labelPx = 12;
function sizeCanvas() {
  const r = canvas.getBoundingClientRect();
  labelPx = Math.max(18, parseFloat(getComputedStyle(document.body).fontSize));
  canvas.width = Math.max(1, Math.round(r.width * devicePixelRatio));
  canvas.height = Math.max(1, Math.round(r.height * devicePixelRatio));
}
new ResizeObserver(sizeCanvas).observe(canvas);

const RING_S = 6; // how long one quake's wiggle lasts on the trace

// Each quake event carries only its peak, so the trace draws a damped wiggle that peaks at that value.
function signal(t) {
  let g = 0;
  for (const q of state.quakes) {
    const dt = (t - q.at) / 1000;
    if (dt >= 0 && dt < RING_S) g += q.g * Math.exp(-dt * 1.1) * Math.sin(dt * 2 * Math.PI * 2.2 + 0.4);
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
  const plotW = w - 6 * dpr - gutter;

  ctx.globalAlpha = connected ? 1 : 0.35;
  ctx.strokeStyle = 'rgba(120,170,235,0.18)';
  ctx.lineWidth = dpr;
  ctx.beginPath();
  for (const g of [-1, 1]) { ctx.moveTo(gutter, mid - g * scale); ctx.lineTo(w, mid - g * scale); }
  ctx.stroke();
  ctx.fillStyle = 'rgba(143,166,198,0.9)';
  ctx.textBaseline = 'middle';
  ctx.fillText('+1 g', 4 * dpr, mid - scale);
  ctx.fillText('-1 g', 4 * dpr, mid + scale);
  // Offline the middle holds the "No live signal" text instead.
  if (connected) {
    ctx.fillText('0 g', 4 * dpr, mid);
    ctx.save();
    ctx.strokeStyle = 'rgba(120,170,235,0.25)';
    ctx.setLineDash([2 * dpr, 4 * dpr]);
    ctx.beginPath();
    ctx.moveTo(gutter, mid);
    ctx.lineTo(w, mid);
    ctx.stroke();
    ctx.restore();
  }
  ctx.textBaseline = 'alphabetic';
  ctx.fillText('60 s ago', gutter, h - fs * 0.3);
  ctx.textAlign = 'right';
  ctx.fillText('now', gutter + plotW, h - fs * 0.3);
  ctx.textAlign = 'left';
  ctx.globalAlpha = 1;

  // Offline there is no live signal, so draw no line rather than a flat one that reads as calm.
  if (!connected) {
    ctx.font = `${Math.max(18, labelPx) * dpr}px system-ui, sans-serif`;
    ctx.fillStyle = '#8fa6c6';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('No live signal', gutter + plotW / 2, mid);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    requestAnimationFrame(drawTrace);
    return;
  }
  const start = now - TRACE_WINDOW_MS;
  const trace = new Path2D();
  const steps = Math.min(w, 1200);
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

const ANSWERS = { ok: 'I\'m okay', help: 'Help', no_answer: 'No answer' };

function render() {
  const { word, detail, note } = statusText(state.status, { alert: Boolean(state.alert), linked: connected });
  document.body.dataset.status = state.status;
  document.body.dataset.link = connected ? 'up' : 'down';
  $('word').textContent = word;
  $('detail').textContent = detail;
  $('note').hidden = !note;
  $('note').textContent = note ?? '\u00a0'; // one blank line keeps the hidden note's height

  $('say').textContent = state.say ? `"${state.say.text}"` : connected ? 'No prompt yet' : 'Prompt unavailable';
  $('say-try').textContent = state.say?.tryNum ? `try ${state.say.tryNum}` : '';
  const heard = state.heard;
  $('heard').textContent = heard ? (heard.transcript ? `"${heard.transcript}"` : '') : connected ? 'No reply yet' : 'Reply unavailable';
  $('heard-chip').hidden = !heard;
  $('heard-chip').className = `chip ${heard?.answer ?? ''}`;
  $('heard-chip').textContent = heard ? ANSWERS[heard.answer] ?? heard.answer : '';

  const a = state.alert;
  $('banner').hidden = !a;
  $('alert-count').hidden = !a;
  if (a) {
    $('alert-source').textContent = a.source;
    $('alert-event').textContent = [a.event, a.severity].filter(Boolean).join(', ');
    $('alert-headline').textContent = a.headline;
    $('alert-area').textContent = a.area;
    $('alert-area').hidden = a.headline.includes(a.area);
  }

  $('battery').hidden = !state.onBattery;
  $('battery-text').textContent = state.batteryPct == null ? 'On battery' : `On battery, ${state.batteryPct}%`;

  $('scale-mark').hidden = !connected || state.indoorF == null;
  if (state.indoorF != null) $('scale-mark').style.setProperty('--at', clamp((state.indoorF - 50) / 50, 0, 1));
  $('temp').innerHTML = state.indoorF == null ? '<small>No reading yet</small>' : `${Math.round(state.indoorF)}<small> &deg;F</small>`;
  $('heat-sub').textContent = !connected ? `${state.indoorF == null ? '' : 'Last known reading. '}No live heat data`
    : a && /heat/i.test(a.event) ? `${a.source}: ${a.event}` : 'No heat alerts';

  $('hub').classList.toggle('bad', !connected);
  $('hub-text').textContent = connected ? 'Hub connected' : 'Hub disconnected';

  renderQuake();
  renderMap();
}

function connect() {
  const ws = new WebSocket(hubUrl);
  ws.onopen = () => { connected = true; render(); };
  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    state = reduce(state, msg, Date.now());
    render();
  };
  ws.onclose = () => {
    connected = false;
    render();
    setTimeout(connect, RETRY_MS);
  };
}

function tick() {
  $('clock').textContent = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  renderQuake();
}
setInterval(tick, 1000);
tick();
render();
connect();
