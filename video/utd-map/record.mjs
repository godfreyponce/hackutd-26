/* Render the UTD 3D campus fly-through to an MP4, one frame at a time.
   Not a screen recording: for every frame the camera is placed exactly, the script waits until every tile for that
   view has loaded, and only then grabs the picture. So a slow machine takes longer but the video never stutters,
   drops a frame or shows a half-loaded building.
     node record.mjs                 -> out/utd-flythrough.mp4 (path from shot.json)
     node record.mjs --shot my.json  -> another path
     node record.mjs --preview       -> every 6th frame at 960x540, for checking a path fast
     node record.mjs --serve         -> just serve the viewer at http://127.0.0.1:5190/ to fly around by hand */

import { createServer } from "node:http";
import { readFileSync, mkdirSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { extname, join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const HERE = dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : d; };
const flag = (n) => process.argv.includes(n);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── static server for viewer/ (no dependencies) ── */
const ROOT = join(HERE, "viewer");
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".glb": "model/gltf-binary", ".png": "image/png", ".jpg": "image/jpeg", ".ktx2": "image/ktx2", ".bin": "application/octet-stream" };
const PORT = Number(arg("--port", 5190));
const server = createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const file = resolve(ROOT, "." + (p.endsWith("/") ? p + "index.html" : p));
  if (!file.startsWith(ROOT) || !existsSync(file)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": MIME[extname(file)] ?? "application/octet-stream" });
  res.end(readFileSync(file));
});
await new Promise((r) => server.listen(PORT, "127.0.0.1", r));
const BASE = `http://127.0.0.1:${PORT}/`;
if (flag("--serve")) { console.log(`viewer: ${BASE}  (Ctrl+C to stop)`); await new Promise(() => {}); }

/* ── the camera path: Barry-Goldman (non-uniform Catmull-Rom) through the keys, so uneven key spacing stays smooth ── */
const shot = JSON.parse(readFileSync(resolve(HERE, arg("--shot", "shot.json")), "utf8"));
const preview = flag("--preview");
const W = preview ? shot.width / 2 : shot.width, H = preview ? shot.height / 2 : shot.height;
const keys = shot.keys;
const T = keys.map((k) => k.t), dur = T[T.length - 1];
const lerp = (a, b, s) => a.map((v, i) => v + (b[i] - v) * s);
function spline(P, t) {
  let i = 0;
  while (i < T.length - 2 && t > T[i + 1]) i++;
  const t1 = T[i], t2 = T[i + 1];
  const t0 = i > 0 ? T[i - 1] : 2 * t1 - t2, t3 = i + 2 < T.length ? T[i + 2] : 2 * t2 - t1;
  const p1 = P[i], p2 = P[i + 1];
  const p0 = i > 0 ? P[i - 1] : lerp(p1, p2, -1), p3 = i + 2 < P.length ? P[i + 2] : lerp(p2, p1, -1);
  const A1 = lerp(p0, p1, (t - t0) / (t1 - t0)), A2 = lerp(p1, p2, (t - t1) / (t2 - t1)), A3 = lerp(p2, p3, (t - t2) / (t3 - t2));
  const B1 = lerp(A1, A2, (t - t0) / (t2 - t0)), B2 = lerp(A2, A3, (t - t1) / (t3 - t1));
  return lerp(B1, B2, (t - t1) / (t2 - t1));
}
const ease = (x) => x * x * x * (x * (6 * x - 15) + 10); // smootherstep: starts and stops with zero speed and acceleration
const moving = Math.round(dur * shot.fps), total = moving + Math.round((shot.hold ?? 0) * shot.fps);
const pose = (f) => { const t = ease(Math.min(1, f / moving)) * dur; return [spline(keys.map((k) => k.pos), t), spline(keys.map((k) => k.look), t)]; };

/* ── browser: GPU first, CPU fallback (slower, same picture) ── */
const { chromium } = await import("playwright");
const MODES = [["--enable-gpu", "--use-angle=d3d11", "--ignore-gpu-blocklist"], ["--enable-gpu", "--ignore-gpu-blocklist"], []];
let browser;
for (const args of MODES) {
  const b = await chromium.launch({ headless: true, args });
  const p = await b.newPage();
  await p.setContent("<canvas></canvas>");
  if (await p.evaluate(() => !!document.querySelector("canvas").getContext("webgl2"))) { await p.close(); browser = b; console.log(`browser: ${args.join(" ") || "default"}`); break; }
  await b.close();
}
if (!browser) throw new Error("no WebGL2 in headless Chromium: run `npx playwright install chromium`");

const OUT = resolve(HERE, "out"), FRAMES = join(OUT, "frames");
rmSync(FRAMES, { recursive: true, force: true });
mkdirSync(FRAMES, { recursive: true });
try {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(`${BASE}?embed=1&record=1`, { waitUntil: "load" });
  await page.waitForFunction(() => window.__utd3d && window.__utd3d.ready().source, null, { timeout: 120_000 });

  /* place the camera, then pump until nothing is loading and no new tile arrived twice in a row */
  const settle = async (pos, look) => {
    await page.evaluate(([p, l]) => window.__utd3d.pose(p, l), [pos, look]);
    let last = -1, calm = 0;
    for (let i = 0; i < 600 && calm < 2; i++) {
      const r = await page.evaluate(() => { const u = window.__utd3d; u.pump(2); return u.ready(); });
      calm = !r.loading && r.tilesEver === last ? calm + 1 : 0;
      last = r.tilesEver;
      if (calm < 2) await sleep(r.loading ? 40 : 10);
    }
  };
  /* warm-up: visit every key so the whole route is in the tile cache before frame 1 */
  for (const k of keys) await settle(k.pos, k.look);

  const step = preview ? 6 : 1;
  let size = null, n = 0;
  const t0 = Date.now();
  for (let f = 0; f <= total; f += step) {
    const [pos, look] = pose(f);
    await settle(pos, look);
    const r = await page.evaluate((lab) => { const u = window.__utd3d; const c = u.gl.domElement; return { url: u.frame(lab, "image/jpeg"), w: c.width, h: c.height }; }, !!shot.labels);
    if (!size) size = [r.w, r.h];
    if (r.w !== size[0] || r.h !== size[1]) throw new Error(`frame ${f}: size changed ${size} -> ${r.w}x${r.h}`);
    writeFileSync(join(FRAMES, `${String(n++).padStart(5, "0")}.jpg`), Buffer.from(r.url.split(",")[1], "base64"));
    if (n % 60 === 0) console.log(`frame ${f}/${total}  ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  const health = await page.evaluate(() => window.__utd3d.ready());
  if (health.errors || errors.length) throw new Error(`viewer errors: ${health.errors} tile, ${errors.join(" | ")}`);
  console.log(`${n} frames at ${size[0]}x${size[1]}`);

  const mp4 = join(OUT, preview ? "preview.mp4" : "utd-flythrough.mp4");
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(preview ? shot.fps / step : shot.fps), "-i", join(FRAMES, "%05d.jpg"),
    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-r", String(shot.fps), "-movflags", "+faststart", mp4], { stdio: "inherit" });
  const probed = execFileSync("ffprobe", ["-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames,width,height,r_frame_rate", "-of", "csv=p=0", mp4]).toString().trim();
  console.log(`wrote ${mp4}  (ffprobe: ${probed})`);
} finally {
  await browser.close();
  server.close();
}
