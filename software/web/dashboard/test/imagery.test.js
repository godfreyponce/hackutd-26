import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { TILE_SETS, setBounds, setTiles, tileLat, tileLon } from '../imagery.js';
import { UTD } from '../homes.js';

const here = new URL('../', import.meta.url);
const city = JSON.parse(readFileSync(new URL('data/richardson.json', here)));
const [cityTiles, homeTiles] = TILE_SETS;

const covers = (b, { latMin, latMax, lonMin, lonMax }) =>
  b.latMin <= latMin && b.latMax >= latMax && b.lonMin <= lonMin && b.lonMax >= lonMax;

test('tile edges match the web mercator grid', () => {
  assert.equal(tileLon(0, 0), -180);
  assert.equal(tileLon(1, 0), 180);
  assert.ok(Math.abs(tileLat(0, 0) - 85.05113) < 1e-5);
  assert.ok(Math.abs(tileLat(1, 1)) < 1e-9);
});

// At 1920x1080 the map canvas is about 1070x1020 px, and the street data runs
// at least 1 km past the city view on every side. Imagery that covers the
// street data covers the city view too.
test('the city tiles cover the whole street data box', () => {
  const [latMin, lonMin, latMax, lonMax] = city.bbox;
  assert.ok(covers(setBounds(cityTiles), { latMin, latMax, lonMin, lonMax }), JSON.stringify(setBounds(cityTiles)));
});

// The home view at 1920x1080 reaches about 815 m from H000 (HOME_ZOOM in app.js).
test('the close tiles cover 1 km on each side of H000', () => {
  const dLat = 1 / 111.32;
  const dLon = dLat / Math.cos((UTD.lat * Math.PI) / 180);
  const box = { latMin: UTD.lat - dLat, latMax: UTD.lat + dLat, lonMin: UTD.lon - dLon, lonMax: UTD.lon + dLon };
  assert.ok(covers(setBounds(homeTiles), box), JSON.stringify(setBounds(homeTiles)));
});

test('every listed tile is saved as a JPEG, and no other file is in imagery/', () => {
  const listed = TILE_SETS.flatMap(setTiles).map((t) => t.file);
  for (const file of listed) {
    const bytes = readFileSync(new URL(file, here));
    assert.deepEqual([...bytes.subarray(0, 3)], [0xff, 0xd8, 0xff], file);
  }
  const saved = readdirSync(new URL('imagery/', here)).filter((f) => !f.startsWith('.')).map((f) => `imagery/${f}`);
  assert.deepEqual(saved.sort(), [...listed].sort());
});
