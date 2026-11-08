import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const app = readFileSync(new URL('./app.js', import.meta.url), 'utf8');

// The whole <div class="brand"> element, nested divs included.
function brandBlock(page) {
  const start = page.indexOf('<div class="brand">');
  assert.notEqual(start, -1, 'the page has a <div class="brand">');
  let depth = 0;
  for (const m of page.slice(start).matchAll(/<(\/?)div\b[^>]*>/g)) {
    depth += m[1] ? -1 : 1;
    if (depth === 0) return page.slice(start, start + m.index + m[0].length);
  }
  assert.fail('the brand div is never closed');
}

const brand = brandBlock(html);
const visibleText = brand.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
const marks = brand.match(/<img\b[^>]*\bclass="mark"[^>]*>/g) ?? [];
const filledByApp = new Set([...app.matchAll(/\$\('([^']+)'\)/g)].map((m) => m[1]));

test('the header shows the LAND mark once, named for screen readers', () => {
  assert.equal(marks.length, 1);
  assert.match(marks[0], /\bsrc="[^"]*land-mark-white\.svg"/);
  assert.match(marks[0], /\balt="LAND"/);
});

test('the header shows only "Home safety monitor" as text, not the word LAND again', () => {
  assert.equal(visibleText, 'Home safety monitor');
  const brandIds = [...brand.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual(brandIds.filter((id) => filledByApp.has(id)), [], 'app.js writes no text into the header brand');
});

test('every element app.js looks up by id is on the page', () => {
  assert.ok(filledByApp.size > 0);
  for (const id of filledByApp) assert.match(html, new RegExp(`\\sid="${id}"`), id);
});
