// Aerial imagery under the street map: USGS The National Map, USGSImageryOnly
// (public domain), the same source as the home screen. The tiles are saved in
// imagery/ so the page works offline; data/imagery.mjs downloads them once.
// Pure, no DOM.

// Zoom 14 is about 8 m per pixel here, close to the city view at 1920x1080
// (about 9 m per screen px). It covers the street data box. Zoom 16 (about
// 2 m per pixel, the closest zoom the service has here) covers at least 1 km
// on each side of H000, past the home view, so the zoom to the box stays sharp.
export const TILE_SETS = [
  { z: 14, x: [3785, 3791], y: [6597, 6603] },
  { z: 16, x: [15153, 15157], y: [26399, 26402] },
];
export const TILE_PX = 256;

export const tileLon = (x, z) => (x / 2 ** z) * 360 - 180;
export const tileLat = (y, z) => (Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / 2 ** z))) * 180) / Math.PI;

// The lon/lat box a whole set covers, from the outer edges of its tiles.
export function setBounds({ z, x, y }) {
  return { lonMin: tileLon(x[0], z), lonMax: tileLon(x[1] + 1, z), latMin: tileLat(y[1] + 1, z), latMax: tileLat(y[0], z) };
}

export function setTiles({ z, x, y }) {
  const tiles = [];
  for (let ty = y[0]; ty <= y[1]; ty++) {
    for (let tx = x[0]; tx <= x[1]; tx++) {
      tiles.push({ z, x: tx, y: ty, col: tx - x[0], row: ty - y[0], file: `imagery/${z}-${tx}-${ty}.jpg` });
    }
  }
  return tiles;
}
