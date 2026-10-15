// Verifies the inline progressive-enhancement script of _includes/subscribe.html
// by running the *rendered* markup from _site/index.html inside a real DOM.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM, VirtualConsole } from 'jsdom';

// Usage: node subscribe-server/tests/frontend/verify-subscribe.mjs [path/to/index.html]
// Run `bundle exec jekyll build` first; jsdom is installed ad hoc:
//   npm install --no-save jsdom
const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '../../..');
const htmlPath = process.argv[2] || path.join(repoRoot, '_site/index.html');
const built = fs.readFileSync(htmlPath, 'utf8');
const start = built.indexOf('<div class="subscribe-box');
if (start < 0) throw new Error('subscribe module not found in _site/index.html');
const end = built.indexOf('</script>', start) + '</script>'.length;
const fragment = built.slice(start, end);

const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', () => {}); // ignore unrelated homepage scripts

function render() {
  const dom = new JSDOM(
    `<!DOCTYPE html><html><body>${fragment}</body></html>`,
    { runScripts: 'dangerously', virtualConsole }
  );
  const { window } = dom;
  window.fetch = (...args) => (window.__fetchImpl || (() => Promise.reject(new Error('no fetch'))))(...args);
  return window;
}

const results = [];
function check(name, actual, expected) {
  const ok = actual === expected;
  results.push({ name, ok, actual, expected });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : `\n      expected: ${expected}\n      actual:   ${actual}`}`);
}

const settle = () => new Promise((resolve) => setTimeout(resolve, 10));

async function submit(window, email) {
  const form = window.document.querySelector('[data-subscribe-form]');
  form.querySelector('input[name="email"]').value = email;
  form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  await settle();
}

const message = (window) => window.document.querySelector('[data-subscribe-msg]');
const button = (window) => window.document.querySelector('.subscribe-btn');

// 1. client-side validation blocks the request
{
  const window = render();
  let called = 0;
  window.__fetchImpl = () => {
    called += 1;
    return Promise.resolve({ status: 201, json: () => Promise.resolve({ status: 'subscribed' }) });
  };
  await submit(window, 'not-an-email');
  check('invalid email shows the error copy', message(window).textContent, 'Please enter a valid email address.');
  check('invalid email is not sent to the API', String(called), '0');
  check('invalid email sets the error style', String(message(window).className.includes('subscribe-msg-error')), 'true');
}

// 2. successful subscribe
{
  const window = render();
  let body = null;
  window.__fetchImpl = (url, options) => {
    body = JSON.parse(options.body);
    return Promise.resolve({ status: 201, json: () => Promise.resolve({ status: 'subscribed' }) });
  };
  await submit(window, '  Someone@Example.com ');
  check('success message', message(window).textContent, 'Done! You are on the list.');
  check('success style', String(message(window).className.includes('subscribe-msg-ok')), 'true');
  check('input is cleared', window.document.querySelector('input[name="email"]').value, '');
  check('button label restored', button(window).textContent, 'Subscribe');
  check('button re-enabled', String(button(window).disabled), 'false');
  check('email trimmed in payload', body.email, 'Someone@Example.com');
  check('payload carries the source', String(typeof body.source), 'string');
  check('payload carries the honeypot field', String(body.sb_hp), '');
}

// 3. already subscribed
{
  const window = render();
  window.__fetchImpl = () => Promise.resolve({ status: 200, json: () => Promise.resolve({ status: 'already_subscribed' }) });
  await submit(window, 'someone@example.com');
  check('duplicate message', message(window).textContent, 'You are already on the list.');
}

// 4. rate limited
{
  const window = render();
  window.__fetchImpl = () => Promise.resolve({ status: 429, json: () => Promise.resolve({ error: 'rate_limited' }) });
  await submit(window, 'someone@example.com');
  check('rate limit message', message(window).textContent, 'Too many attempts. Please try again later.');
}

// 5. server rejects the address
{
  const window = render();
  window.__fetchImpl = () =>
    Promise.resolve({ status: 400, json: () => Promise.resolve({ error: 'invalid_email', message: 'Please enter a valid email address.' }) });
  await submit(window, 'someone@example.com');
  check('server validation message', message(window).textContent, 'Please enter a valid email address.');
}

// 6. network failure / timeout
{
  const window = render();
  window.__fetchImpl = () => Promise.reject(new Error('offline'));
  await submit(window, 'someone@example.com');
  check('network error message', message(window).textContent, 'Something went wrong. Please try again later.');
  check('button recovers after a failure', String(button(window).disabled), 'false');
}

// 7. honeypot input is hidden from humans
{
  const window = render();
  check('honeypot field exists', String(!!window.document.querySelector('input[name="sb_hp"]')), 'true');
  check('honeypot is aria-hidden', window.document.querySelector('.subscribe-hp').getAttribute('aria-hidden'), 'true');
}

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exit(failed.length === 0 ? 0 : 1);
