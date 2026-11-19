// gta6-meme-x-01 — the entrypoint.
// The gate hands over a bot directory holding POST.json, the address of the post the house
// reads, and wants the same name written back into the output directory as one clean record.
// Everything below is address hygiene: take the shapes X really prints, fold them into a
// single canonical form, and refuse the rest with exactly one readable line on stderr.
// No clock, no randomness, no network — a second run on the same input agrees byte for byte.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import * as path from 'node:path';

const BOT_DIR_DEFAULT = '/bot';
const OUT_DIR_DEFAULT = '/output';
const POST_FILE = 'POST.json';
const EXIT_FAILURE = 1;

const ID_SHAPE = /^[0-9]{1,25}$/;
const SCHEME_PREFIX = /^[a-z][a-z0-9+.-]*:\/\//i;
const HANDLE_SHAPE = /^[A-Za-z0-9_.-]{1,30}$/;
const KNOWN_HOSTS = new Set(['x.com', 'twitter.com']);
const HOST_PREFIXES = ['www.', 'mobile.'];

function bail(reason: string): never {
  console.error(reason);
  process.exit(EXIT_FAILURE);
}

// Run one risky call and turn its failure into the single stderr line the contract asks for.
function attempt<T>(work: () => T, complaint: (err: unknown) => string): T {
  try { return work(); } catch (err) { bail(complaint(err)); }
}

function flatten(err: unknown): string {
  const text = err instanceof Error ? err.message : String(err);
  const squeezed = text.replace(/\s+/g, ' ').trim();
  return squeezed.length > 0 ? squeezed : 'unknown error';
}

function describe(value: unknown): string {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'an array';
  if (typeof value === 'undefined') return 'undefined';
  return typeof value === 'object' ? 'an object' : `a ${typeof value}`;
}

function stripHostPrefixes(hostname: string): string {
  let host = hostname.toLowerCase();
  for (const prefix of HOST_PREFIXES) {
    if (host.startsWith(prefix)) {
      host = host.slice(prefix.length);
    }
  }
  return host;
}

// Fold whatever address we were given into https://x.com/<user>/status/<id>, or into
// https://x.com/i/web/status/<id> for the web form and for a bare numeric id.
function canonicalise(candidate: string): string {
  const trimmed = candidate.trim();

  if (ID_SHAPE.test(trimmed)) {
    return `https://x.com/i/web/status/${trimmed}`;
  }

  const deSchemed = trimmed.replace(SCHEME_PREFIX, '');
  const stopAt = deSchemed.search(/[?#]/);
  const address = stopAt === -1 ? deSchemed : deSchemed.slice(0, stopAt);
  const chunks = address.replace(/^\/\//, '').split('/');

  const hostname = stripHostPrefixes(chunks.shift() ?? '');
  const segments = chunks.filter((chunk) => chunk.length > 0);

  if (!KNOWN_HOSTS.has(hostname)) {
    bail(`${POST_FILE} url is not an X or Twitter post address: ${candidate}`);
  }

  const webForm = segments.length === 4 && segments[0] === 'i' && segments[1] === 'web' && segments[2] === 'status';
  if (webForm && ID_SHAPE.test(segments[3])) {
    return `https://x.com/i/web/status/${segments[3]}`;
  }

  const userForm = segments.length === 3 && segments[1] === 'status';
  if (userForm) {
    const handle = segments[0].replace(/^@/, '');
    if (HANDLE_SHAPE.test(handle) && ID_SHAPE.test(segments[2])) {
      return `https://x.com/${handle}/status/${segments[2]}`;
    }
  }

  bail(`${POST_FILE} url is not an X or Twitter post address: ${candidate}`);
}

function loadPost(botDir: string): unknown {
  const source = path.join(botDir, POST_FILE);

  if (!existsSync(source)) {
    bail(`${POST_FILE} is missing from the bot directory ${botDir}`);
  }

  const raw = attempt(() => readFileSync(source, 'utf8'), (err) => `${POST_FILE} in ${botDir} could not be read: ${flatten(err)}`);
  return attempt(() => JSON.parse(raw) as unknown, (err) => `${POST_FILE} in ${botDir} is not valid JSON: ${flatten(err)}`);
}

function urlFrom(record: unknown, botDir: string): string {
  if (typeof record !== 'object' || record === null || Array.isArray(record)) {
    bail(`${POST_FILE} in ${botDir} must hold a JSON object, found ${describe(record)}`);
  }

  const fields = record as Record<string, unknown>;
  if (!('url' in fields)) {
    bail(`${POST_FILE} in ${botDir} has no "url" field`);
  }

  const candidate = fields.url;
  if (typeof candidate !== 'string') {
    bail(`${POST_FILE} in ${botDir} has a "url" field that is ${describe(candidate)}, not a string`);
  }
  if (candidate.trim().length === 0) {
    bail(`${POST_FILE} in ${botDir} has an empty "url" field`);
  }

  return canonicalise(candidate);
}

function main(): void {
  const botDir = process.env.MAKEFUN_BOT_DIR ?? BOT_DIR_DEFAULT;
  const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? OUT_DIR_DEFAULT;

  const postUrl = urlFrom(loadPost(botDir), botDir);
  const payload = `${JSON.stringify({ url: postUrl })}\n`;
  const target = path.join(outDir, POST_FILE);

  attempt(
    () => {
      mkdirSync(outDir, { recursive: true });
      writeFileSync(target, payload, 'utf8');
    },
    (err) => `${POST_FILE} could not be written to ${outDir}: ${flatten(err)}`
  );
}

main();
