import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// The landing page at / sits one level up and has no test package of its own.
const html = readFileSync(new URL('../../index.html', import.meta.url), 'utf8');
const headings = [...html.matchAll(/<h1\b[^>]*>([\s\S]*?)<\/h1>/g)].map((m) => m[1]).join(' ');
const visibleText = headings.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
const marks = headings.match(/<img\b[^>]*\ssrc="[^"]*land-mark-white\.svg"[^>]*>/g) ?? [];

test('the landing page heading shows the LAND mark once, named for screen readers', () => {
  assert.equal(marks.length, 1);
  assert.match(marks[0], /\salt="LAND"/);
});

test('the landing page heading shows no word LAND next to the mark', () => {
  assert.equal(visibleText, '');
});
