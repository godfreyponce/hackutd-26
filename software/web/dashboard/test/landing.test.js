import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// The landing page at / sits one level up and has no test package of its own.
const html = readFileSync(new URL('../../index.html', import.meta.url), 'utf8');
const headings = [...html.matchAll(/<h1\b[^>]*>([\s\S]*?)<\/h1>/g)].map((m) => m[1]).join(' ');
const visibleText = headings.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
const wordmarks = headings.match(/<img\b[^>]*\ssrc="[^"]*land-wordmark-white\.svg"[^>]*>/g) ?? [];

test('the landing page heading shows the LAND wordmark with its tagline once, named for screen readers', () => {
  assert.equal(wordmarks.length, 1);
  assert.match(wordmarks[0], /\salt="LAND: Life Against Natural Disaster"/);
});

test('the landing page heading shows no text next to the wordmark', () => {
  assert.equal(visibleText, '');
});
