import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as common from './common.js';
const { ago } = common;

test('ago reads in seconds, then minutes, then hours', () => {
  assert.equal(ago(0, 400), 'just now');
  assert.equal(ago(0, 12_400), '12 s ago');
  assert.equal(ago(0, 3 * 60_000 + 59_000), '3 min ago');
  assert.equal(ago(0, 2 * 3_600_000 + 5), '2 h ago');
});

test('ago with no time is a dash', () => {
  assert.equal(ago(null, 1000), '--');
});

test('the offline head line has one form on every screen', () => {
  const { offlineLine } = common;
  assert.equal(offlineLine({ connected: true, linkAt: 5 }, 'No active hazard'), null);
  assert.equal(offlineLine({ connected: false, linkAt: null }, 'No active hazard'), 'Hub offline. Nothing received yet');
  assert.equal(offlineLine({ connected: false, linkAt: 5 }, 'Someone is still'), 'Hub offline. Last known: someone is still');
  assert.equal(offlineLine({ connected: false, linkAt: 5 }, 'USGS Earthquake showing'), 'Hub offline. Last known: USGS Earthquake showing');
});
