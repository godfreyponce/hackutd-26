// Base map: the dark globe (Natural Earth) and the Richardson street map
// (OpenStreetMap) over USGS aerial imagery. Loads only the vendored files in
// data/ and imagery/. Needs the vendored d3-geo, loaded as a classic script
// before the page module.
import { TILE_SETS, TILE_PX, setBounds, setTiles } from './imagery.js';

const { geoPath, geoGraticule10, geoCentroid, geoDistance } = globalThis.d3;

export const PALETTE = {
  space: '#04060a',
  ocean: '#0a111c',
  oceanEdge: '#05080e',
  land: '#141b25',
  landClear: 'rgba(20, 27, 37, 0)',
  coast: '#2a3647',
  border: 'rgba(120, 140, 165, 0.28)',
  state: 'rgba(120, 140, 165, 0.14)',
  texas: 'rgba(160, 185, 215, 0.5)',
  graticule: 'rgba(110, 140, 180, 0.07)',
  glow: '100, 160, 255',
  // Laid over the aerial imagery so the dots, red roads and labels stay on top.
  imageryDim: 'rgba(4, 8, 14, 0.52)',
  // Offline the page greys and darkens the whole map; the darker imagery keeps the grey dots findable.
  imageryDimOffline: 'rgba(4, 8, 14, 0.75)',
  waterway: 'rgba(90, 160, 220, 0.35)',
  rail: 'rgba(200, 210, 225, 0.25)',
  road: {
    minor: 'rgba(200, 215, 235, 0.10)',
    tertiary: 'rgba(200, 215, 235, 0.18)',
    major: 'rgba(210, 222, 240, 0.28)',
    link: 'rgba(210, 222, 240, 0.24)',
    motorway: 'rgba(220, 230, 245, 0.42)',
  },
};
// Road widths in px at the city view; they grow a little when zoomed in.
const ROAD_PX = { minor: 0.7, tertiary: 1.1, major: 1.6, link: 1, motorway: 2.6 };
const RED_ROAD_PX = { minor: 1.1, tertiary: 1.5, major: 2.2, link: 1.4, motorway: 3.2 };
const ROAD_ORDER = ['minor', 'tertiary', 'link', 'major', 'motorway'];
const RAD = Math.PI / 180;

async function getJson(name) {
  const res = await fetch(new URL(`data/${name}`, import.meta.url));
  if (!res.ok) throw new Error(`data/${name}: ${res.status}`);
  return res.json();
}

// The street data is stored in 1e-5 degree steps from an origin. Paths are
// built once in a flat local frame (x scaled by cos(lat) so 1 unit is the same
// length both ways) and placed on screen with one affine transform per frame.
// At city zoom the orthographic projection is flat to well under a pixel.
function cityPaths(city) {
  const kx = Math.cos(city.origin[1] * RAD);
  const addLine = (path, flat) => {
    let x = 0;
    let y = 0;
    for (let i = 0; i < flat.length; i += 2) {
      x += flat[i];
      y += flat[i + 1];
      if (i === 0) path.moveTo(x * kx, -y);
      else path.lineTo(x * kx, -y);
    }
  };
  const lines = (list) => {
    const p = new Path2D();
    for (const l of list) addLine(p, l);
    return p;
  };
  return {
    roads: Object.fromEntries(Object.entries(city.roads).map(([k, v]) => [k, lines(v)])),
    rail: lines(city.rail),
    waterways: lines(city.waterways),
  };
}

// Each fine land polygon with a bounding circle (radians), so a zoomed-in
// frame only sends the polygons near the view through d3.
function landParts(land) {
  return land.coordinates.map((poly) => {
    const center = geoCentroid({ type: 'Polygon', coordinates: poly });
    const radius = Math.max(...poly[0].map((p) => geoDistance(center, p)));
    return { poly, center, radius };
  });
}

async function getImage(file) {
  const img = new Image();
  img.src = new URL(file, import.meta.url).href;
  await img.decode();
  return img;
}

const IMAGERY_FILTER = 'saturate(1.35) contrast(1.05)';

// One canvas per tile set, so each set is one drawImage with no seams between tiles.
async function mosaic(set) {
  const tiles = setTiles(set);
  const images = await Promise.all(tiles.map((t) => getImage(t.file)));
  const canvas = document.createElement('canvas');
  canvas.width = (set.x[1] - set.x[0] + 1) * TILE_PX;
  canvas.height = (set.y[1] - set.y[0] + 1) * TILE_PX;
  const g = canvas.getContext('2d');
  // Done once here, not per frame: brings the lawns and trees back up under the dim.
  g.filter = IMAGERY_FILTER;
  tiles.forEach((t, i) => g.drawImage(images[i], t.col * TILE_PX, t.row * TILE_PX));
  return { canvas, bounds: setBounds(set) };
}

export async function loadBasemap() {
  const [world, city, imagery] = await Promise.all([
    getJson('world.json'),
    getJson('richardson.json'),
    // The streets and the globe still draw if the imagery fails.
    Promise.all(TILE_SETS.map(mosaic)).catch((err) => {
      console.error('Imagery did not load:', err);
      return null;
    }),
  ]);
  return { world, city, imagery, landParts: landParts(world.land), paths: cityPaths(city), graticule: geoGraticule10() };
}

// Whole globe: the coarse land. Zoomed in: only the fine polygons in view.
function landInView(map, proj, w, h, globeZoom) {
  if (globeZoom < 3) return map.world.landCoarse;
  const [lon, lat] = proj.rotate();
  const center = [-lon, -lat];
  const reach = Math.asin(Math.min(1, Math.hypot(w, h) / 2 / proj.scale()));
  const coordinates = map.landParts.filter((p) => geoDistance(p.center, center) - p.radius < reach).map((p) => p.poly);
  return { type: 'MultiPolygon', coordinates };
}

// Screen px per stored unit, and where the origin lands, for this projection.
export function cityFrame(map, proj) {
  const [ax, ay] = proj(map.city.origin);
  return { ax, ay, s: (proj.scale() * RAD) / map.city.units };
}

// globeZoom: projection scale over the whole-globe view scale.
export function drawGlobe(c, map, proj, w, h, globeZoom) {
  const [cx, cy] = proj.translate();
  const r = proj.scale();
  const path = geoPath(proj, c);

  const glow = c.createRadialGradient(cx, cy, r * 0.98, cx, cy, r * 1.14);
  glow.addColorStop(0, `rgba(${PALETTE.glow}, 0.22)`);
  glow.addColorStop(1, `rgba(${PALETTE.glow}, 0)`);
  c.fillStyle = glow;
  c.fillRect(0, 0, w, h);

  const ocean = c.createRadialGradient(cx - r * 0.35, cy - r * 0.4, r * 0.1, cx, cy, r);
  ocean.addColorStop(0, PALETTE.ocean);
  ocean.addColorStop(1, PALETTE.oceanEdge);
  c.beginPath();
  path({ type: 'Sphere' });
  c.fillStyle = ocean;
  c.fill();

  // The graticule only reads on the whole globe; past that it costs time.
  if (globeZoom < 4) {
    c.beginPath();
    path(map.graticule);
    c.strokeStyle = PALETTE.graticule;
    c.lineWidth = 1;
    c.stroke();
  }

  c.beginPath();
  path(landInView(map, proj, w, h, globeZoom));
  c.fillStyle = PALETTE.land;
  c.fill();
  c.strokeStyle = PALETTE.coast;
  c.lineWidth = 0.8;
  c.stroke();

  c.beginPath();
  path(map.world.states);
  c.strokeStyle = PALETTE.state;
  c.lineWidth = 0.6;
  c.stroke();

  c.beginPath();
  path(map.world.borders);
  c.strokeStyle = PALETTE.border;
  c.lineWidth = 0.8;
  c.stroke();

  c.beginPath();
  path(map.world.texas);
  c.strokeStyle = PALETTE.texas;
  c.lineWidth = 1.2;
  c.stroke();

  // Light from the upper left, shade toward the limb: reads as a sphere.
  const shade = c.createRadialGradient(cx - r * 0.45, cy - r * 0.5, 0, cx, cy, r);
  shade.addColorStop(0, 'rgba(255, 255, 255, 0.05)');
  shade.addColorStop(0.6, 'rgba(0, 0, 0, 0)');
  shade.addColorStop(1, 'rgba(0, 0, 0, 0.45)');
  c.beginPath();
  path({ type: 'Sphere' });
  c.fillStyle = shade;
  c.fill();
}

function placeCity(c, map, proj, dpr) {
  const { ax, ay, s } = cityFrame(map, proj);
  c.setTransform(dpr * s, 0, 0, dpr * s, dpr * ax, dpr * ay);
  return s;
}

// The close set only adds detail past the city zoom, so it fades in on the way to H000.
const CLOSE_FADE = [1.5, 3];

// Draws in the city frame set by placeCity: x is lon scaled by cos(lat), y is -lat, both in stored units.
function drawImagery(c, map, alpha, zoomIn, offline) {
  if (!map.imagery) return;
  const { origin, units } = map.city;
  const kx = Math.cos(origin[1] * RAD);
  const rect = (b) => [(b.lonMin - origin[0]) * units * kx, (origin[1] - b.latMax) * units, (b.lonMax - b.lonMin) * units * kx, (b.latMax - b.latMin) * units];
  const [wide, close] = map.imagery;
  const closeShare = Math.min(1, Math.max(0, (zoomIn - CLOSE_FADE[0]) / (CLOSE_FADE[1] - CLOSE_FADE[0])));
  // The default 'low' skips pixels when the mosaic shrinks on the flight from the globe, which shimmers.
  c.imageSmoothingQuality = 'high';
  c.drawImage(wide.canvas, ...rect(wide.bounds));
  if (closeShare > 0) {
    c.globalAlpha = alpha * closeShare;
    c.drawImage(close.canvas, ...rect(close.bounds));
  }
  c.globalAlpha = alpha;
  c.fillStyle = offline ? PALETTE.imageryDimOffline : PALETTE.imageryDim;
  c.fillRect(...rect(wide.bounds));
  fadeEdges(c, rect(wide.bounds), EDGE_FADE_KM * (units / 111.32));
}

// Fades the imagery edges into the land color, so the flight from the globe
// shows no hard square. The fade sits outside the city view at 1920x1080.
const EDGE_FADE_KM = 1;

function fadeEdges(c, [x, y, w, h], f) {
  const strips = [
    [x, y, x + f, y, x, y, f, h],
    [x + w, y, x + w - f, y, x + w - f, y, f, h],
    [x, y, x, y + f, x, y, w, f],
    [x, y + h, x, y + h - f, x, y + h - f, w, f],
  ];
  for (const [x0, y0, x1, y1, rx, ry, rw, rh] of strips) {
    const g = c.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, PALETTE.land);
    g.addColorStop(1, PALETTE.landClear);
    c.fillStyle = g;
    c.fillRect(rx, ry, rw, rh);
  }
}

// zoomIn: projection scale over the city view scale (1 at the city view).
export function drawCity(c, map, proj, dpr, alpha, zoomIn, offline) {
  const p = map.paths;
  c.save();
  c.globalAlpha = alpha;
  const s = placeCity(c, map, proj, dpr);
  const grow = Math.min(2.2, Math.max(0.6, Math.sqrt(zoomIn)));
  const px = (n) => (n * grow) / s;
  drawImagery(c, map, alpha, zoomIn, offline);
  c.lineCap = 'round';
  c.lineJoin = 'round';
  c.strokeStyle = PALETTE.waterway;
  c.lineWidth = px(1.2);
  c.stroke(p.waterways);
  c.strokeStyle = PALETTE.rail;
  c.lineWidth = px(1);
  c.setLineDash([px(4), px(3)]);
  c.stroke(p.rail);
  c.setLineDash([]);
  for (const k of ROAD_ORDER) {
    c.strokeStyle = PALETTE.road[k];
    c.lineWidth = px(ROAD_PX[k]);
    c.stroke(p.roads[k]);
  }
  c.restore();
}

export function drawRedRoads(c, map, proj, dpr, zoomIn) {
  c.save();
  const s = placeCity(c, map, proj, dpr);
  const grow = Math.min(2.2, Math.max(0.6, Math.sqrt(zoomIn)));
  c.lineCap = 'round';
  c.lineJoin = 'round';
  c.strokeStyle = '#ff5a4f';
  for (const k of ROAD_ORDER) {
    c.lineWidth = (RED_ROAD_PX[k] * grow) / s;
    c.stroke(map.paths.roads[k]);
  }
  c.restore();
}

export function drawRoadLabels(c, map, proj, alpha) {
  c.save();
  c.globalAlpha = alpha;
  c.font = '700 10px ui-monospace, "SF Mono", Menlo, monospace';
  c.textAlign = 'center';
  c.textBaseline = 'middle';
  for (const l of map.city.labels) {
    const [x, y] = proj([l.lon, l.lat]);
    const w = c.measureText(l.text).width + 10;
    c.fillStyle = '#1d2733';
    c.strokeStyle = '#46576d';
    c.lineWidth = 1;
    c.beginPath();
    c.roundRect(x - w / 2, y - 8, w, 16, 4);
    c.fill();
    c.stroke();
    c.fillStyle = '#b8c4d2';
    c.fillText(l.text, x, y + 0.5);
  }
  c.restore();
}
