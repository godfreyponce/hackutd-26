import { initialState, reduce, statusText, TRACE_WINDOW_MS } from './state.js';

// The product name is not settled. Change it here only.
export const PRODUCT_NAME = 'Lifeline';

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
$('hub-url').textContent = `Hub ${hubUrl}`;

// ---------- neighborhood map ----------

function neighbors() {
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const dots = [];
  for (let row = 0; row < 6; row++) {
    for (let col = 0; col < 7; col++) {
      const x = 22 + col * 43 + (rand() - 0.5) * 22;
      const y = 22 + row * 44 + (rand() - 0.5) * 22;
      if (Math.hypot(x - HOME.x, y - HOME.y) > 24 && rand() > 0.2) dots.push({ x, y });
    }
  }
  return dots;
}

const SVG = 'http://www.w3.org/2000/svg';
function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

const map = $('map');
const wave = svgEl('circle', { class: 'wave', cx: HOME.x, cy: HOME.y, r: 4 });
map.append(wave);
const neighborDots = neighbors().map(({ x, y }) => {
  const el = svgEl('circle', { class: 'node', cx: x, cy: y, r: 5 });
  el.style.transitionDelay = `${Math.round(Math.hypot(x - HOME.x, y - HOME.y) * 8)}ms`;
  map.append(el);
  return el;
});
map.append(svgEl('circle', { class: 'ring', cx: HOME.x, cy: HOME.y, r: 13 }));
const homeDot = svgEl('circle', { class: 'node', cx: HOME.x, cy: HOME.y, r: 7 });
map.append(homeDot);
const homeLabel = svgEl('text', { x: HOME.x, y: HOME.y + 30, 'text-anchor': 'middle', fill: '#8fa6c6', 'font-size': 13 });
homeLabel.textContent = 'H000';
map.append(homeLabel);

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
  const homeNote = { hit: 'This home was hit', ok: 'This home is okay', idle: '' }[state.home];
  $('map-sub').textContent = state.areaHit ? `Quake hit the neighborhood. ${homeNote}.` : homeNote ? `${homeNote}.` : 'All homes quiet';
}

// ---------- seismic trace ----------

const canvas = $('trace');
const ctx = canvas.getContext('2d');

function sizeCanvas() {
  const r = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.round(r.width * devicePixelRatio));
  canvas.height = Math.max(1, Math.round(r.height * devicePixelRatio));
}
new ResizeObserver(sizeCanvas).observe(canvas);

// Each quake event carries only its peak, so the trace draws a damped wiggle that peaks at that value.
function signal(t) {
  let g = 0;
  for (const q of state.quakes) {
    const dt = (t - q.at) / 1000;
    if (dt >= 0 && dt < 6) g += q.g * Math.exp(-dt * 1.1) * Math.sin(dt * 2 * Math.PI * 2.2 + 0.4);
  }
  return g;
}

function drawTrace() {
  const now = Date.now();
  const { width: w, height: h } = canvas;
  const dpr = devicePixelRatio;
  ctx.clearRect(0, 0, w, h);
  const maxG = Math.max(1, ...state.quakes.map((q) => q.g)) * 1.15;
  const mid = h / 2;
  const scale = (h / 2 - 4 * dpr) / maxG;

  ctx.strokeStyle = 'rgba(120,170,235,0.18)';
  ctx.lineWidth = dpr;
  ctx.beginPath();
  for (const g of [-1, 0, 1]) { ctx.moveTo(0, mid - g * scale); ctx.lineTo(w, mid - g * scale); }
  ctx.stroke();
  ctx.fillStyle = 'rgba(143,166,198,0.9)';
  ctx.font = `${12 * dpr}px system-ui, sans-serif`;
  ctx.fillText('+1 g', 4 * dpr, mid - scale + 14 * dpr);
  ctx.fillText('-1 g', 4 * dpr, mid + scale - 4 * dpr);
  ctx.fillText('60 s', w - 34 * dpr, h - 4 * dpr);

  ctx.strokeStyle = state.quakes.length ? '#ff6b5a' : '#4da3ff';
  ctx.lineWidth = 2 * dpr;
  ctx.beginPath();
  const steps = Math.min(w, 1200);
  for (let i = 0; i <= steps; i++) {
    const x = (i / steps) * w;
    const t = now - TRACE_WINDOW_MS + (i / steps) * TRACE_WINDOW_MS;
    const y = mid - signal(t) * scale;
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  }
  ctx.stroke();
  requestAnimationFrame(drawTrace);
}
requestAnimationFrame(drawTrace);

function renderQuake() {
  const recent = state.quakes.filter((q) => Date.now() - q.at <= TRACE_WINDOW_MS);
  const last = recent.at(-1);
  $('quake-peak').textContent = last ? `${last.g.toFixed(2)} g` : '';
  $('quake-sub').textContent = last ? `Last peak, ${recent.length} event${recent.length > 1 ? 's' : ''} in the last minute` : 'No shaking in the last minute';
}

// ---------- the rest ----------

const ANSWERS = { ok: 'I\'m okay', help: 'Help', no_answer: 'No answer' };

function render() {
  const { word, detail, note } = statusText(state.status, { alert: Boolean(state.alert) });
  document.body.dataset.status = state.status;
  $('word').textContent = word;
  $('detail').textContent = detail;
  $('note').hidden = !note;
  $('note').textContent = note ?? '';

  $('say').textContent = state.say ? `"${state.say.text}"` : 'Nothing yet';
  $('say-try').textContent = state.say?.tryNum ? `try ${state.say.tryNum}` : '';
  const heard = state.heard;
  $('heard').textContent = heard ? (heard.transcript ? `"${heard.transcript}" (${ANSWERS[heard.answer] ?? heard.answer})` : ANSWERS[heard.answer] ?? heard.answer) : 'Nothing yet';
  $('heard-try').textContent = heard?.tryNum ? `try ${heard.tryNum}` : '';

  const a = state.alert;
  $('banner').hidden = !a;
  $('alert-count').hidden = !a;
  if (a) {
    $('alert-source').textContent = a.source;
    $('alert-event').textContent = [a.event, a.severity].filter(Boolean).join(', ');
    $('alert-headline').textContent = a.headline;
    $('alert-area').textContent = a.area;
  }

  $('battery').hidden = !state.onBattery;
  $('battery-text').textContent = state.batteryPct == null ? 'On battery' : `On battery, ${state.batteryPct}%`;

  $('temp').innerHTML = state.indoorF == null ? '<small>No reading yet</small>' : `${Math.round(state.indoorF)}<small> &deg;F</small>`;
  $('heat-sub').textContent = a && /heat/i.test(a.event) ? `${a.source}: ${a.event}` : 'No heat alerts';

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
