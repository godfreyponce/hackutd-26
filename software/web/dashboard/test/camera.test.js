import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialCamera, cameraEvent, viewAt, arrivalAt, flying, nextStage } from '../camera.js';

const VIEWS = {
  world: { lon: -96.75, lat: 25, scale: 300 },
  city: { lon: -96.75, lat: 32.985, scale: 400000 },
  home: { lon: -96.7502, lat: 32.9857, scale: 1600000 },
};

const close = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);
const sameView = (a, b) => {
  close(a.lon, b.lon);
  close(a.lat, b.lat);
  close(a.scale, b.scale, 1e-3);
};

test('idle: the globe starts in the world stage and turns slowly', () => {
  const cam = initialCamera(0, VIEWS);
  assert.equal(cam.stage, 'world');
  const a = viewAt(cam, 0, VIEWS);
  const b = viewAt(cam, 1000, VIEWS);
  assert.equal(a.scale, VIEWS.world.scale);
  assert.ok(b.lon !== a.lon);
});

test('quake flies from the world to the city and lands on the city view', () => {
  const cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 5000, VIEWS);
  assert.equal(cam.stage, 'city');
  assert.ok(flying(cam, 5001));
  assert.ok(arrivalAt(cam) > 5000);
  sameView(viewAt(cam, arrivalAt(cam), VIEWS), VIEWS.city);
});

test('quake: the globe turns to face the city before the camera flies down', () => {
  const start = viewAt(initialCamera(0, VIEWS), 30000, VIEWS);
  const cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 30000, VIEWS);
  const early = viewAt(cam, cam.at + cam.ms * 0.25, VIEWS);
  assert.ok(early.scale < VIEWS.world.scale * 1.5, 'still zoomed out');
  assert.ok(Math.abs(early.lon - start.lon) > 1, 'already turning');
});

test('a second quake while in the city changes nothing', () => {
  const cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 0, VIEWS);
  assert.equal(cameraEvent(cam, 'quake', 9000, VIEWS), cam);
});

test('alarm zooms to the home; clear eases back to the city', () => {
  let cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 0, VIEWS);
  cam = cameraEvent(cam, 'alarm', 10000, VIEWS);
  assert.equal(cam.stage, 'home');
  sameView(viewAt(cam, arrivalAt(cam), VIEWS), VIEWS.home);
  cam = cameraEvent(cam, 'clear', 20000, VIEWS);
  assert.equal(cam.stage, 'city');
  sameView(viewAt(cam, arrivalAt(cam), VIEWS), VIEWS.city);
});

test('alarm before any quake still goes to the home', () => {
  assert.equal(cameraEvent(initialCamera(0, VIEWS), 'alarm', 0, VIEWS).stage, 'home');
});

test('clear outside the home view changes nothing', () => {
  const cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 0, VIEWS);
  assert.equal(cameraEvent(cam, 'clear', 9000, VIEWS), cam);
});

test('reset flies back to the globe, which turns again after landing', () => {
  let cam = cameraEvent(initialCamera(0, VIEWS), 'alarm', 0, VIEWS);
  cam = cameraEvent(cam, 'reset', 10000, VIEWS);
  assert.equal(cam.stage, 'world');
  const landed = viewAt(cam, arrivalAt(cam), VIEWS);
  sameView(landed, VIEWS.world);
  assert.ok(viewAt(cam, arrivalAt(cam) + 1000, VIEWS).lon !== landed.lon);
});

test('v steps world, city, home and back to world', () => {
  assert.equal(nextStage('world', 'v'), 'city');
  assert.equal(nextStage('city', 'v'), 'home');
  assert.equal(nextStage('home', 'v'), 'world');
});

test('an event mid-flight starts from where the camera is', () => {
  let cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 0, VIEWS);
  const mid = cam.at + cam.ms / 2;
  const here = viewAt(cam, mid, VIEWS);
  cam = cameraEvent(cam, 'alarm', mid, VIEWS);
  sameView(viewAt(cam, mid, VIEWS), here);
});

test('reduced motion cuts: the new view shows at once', () => {
  const cam = cameraEvent(initialCamera(0, VIEWS), 'quake', 100, VIEWS, { reduced: true });
  assert.equal(flying(cam, 100), false);
  sameView(viewAt(cam, 100, VIEWS), VIEWS.city);
});

test('reduced motion: the idle globe does not turn', () => {
  const cam = initialCamera(0, VIEWS, { reduced: true });
  assert.equal(viewAt(cam, 0, VIEWS).lon, viewAt(cam, 60000, VIEWS).lon);
  const back = cameraEvent(cameraEvent(cam, 'quake', 0, VIEWS, { reduced: true }), 'reset', 10, VIEWS, { reduced: true });
  assert.equal(viewAt(back, 10, VIEWS).lon, viewAt(back, 60000, VIEWS).lon);
});

test('the turn takes the short way across the date line', () => {
  const views = { ...VIEWS, city: { lon: -170, lat: 0, scale: 400000 }, world: { lon: 170, lat: 0, scale: 300 } };
  let cam = initialCamera(0, views);
  cam = cameraEvent(cam, 'quake', 0, views);
  const v = viewAt(cam, cam.ms * 0.2, views);
  assert.ok(v.lon > 170 || v.lon < -170, `went the long way: ${v.lon}`);
});
