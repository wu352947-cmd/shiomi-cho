#!/usr/bin/env node
// Headless-Chrome screenshot harness (software WebGL2 via SwiftShader).
// Usage: node tools/shot.mjs --out shots/a.png [--w 1280] [--h 720] [--page index.html]
//        [--params "preset=golden&cam=hero"] [--wait 800] [--eval "js"] [--timeout 90000]
import http from 'node:http';
import { readFile, stat, mkdir, rm } from 'node:fs/promises';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const argv = process.argv.slice(2);
const arg = (name, def) => { const i = argv.indexOf('--' + name); return i >= 0 ? argv[i + 1] : def; };
const out = resolve(ROOT, arg('out', 'shots/shot.png'));
const width = Number(arg('w', 1280));
const height = Number(arg('h', 720));
const pagePath = arg('page', 'index.html');
const params = arg('params', '');
const waitMs = Number(arg('wait', 900));
const evalScript = arg('eval', '');
const timeout = Number(arg('timeout', 120000));
const chromeBin = arg('chrome', '/usr/bin/google-chrome');

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.bin': 'application/octet-stream', '.woff2': 'font/woff2' };

const server = http.createServer(async (req, res) => {
  try {
    let p = decodeURIComponent((req.url || '/').split('?')[0]);
    if (p.endsWith('/')) p += 'index.html';
    const fp = normalize(join(ROOT, p));
    if (!fp.startsWith(ROOT)) { res.writeHead(403); return res.end('forbidden'); }
    const st = await stat(fp).catch(() => null);
    if (!st || !st.isFile()) { res.writeHead(404); return res.end('nf'); }
    res.writeHead(200, { 'Content-Type': MIME[extname(fp).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(await readFile(fp));
  } catch (e) { res.writeHead(500); res.end(String(e)); }
});
// Serialize headless screenshots across the whole team: software WebGL is CPU-heavy.
const LOCK_DIR = join(ROOT, '.tmp', 'shot.lock');
let lockHeld = false;
for (let waited = 0; ; waited += 2500) {
  try {
    await mkdir(LOCK_DIR, { recursive: true });
    lockHeld = true;
    break;
  } catch (e) {
    if (e && e.code !== 'EEXIST') { console.warn('shot lock warning:', e.message); break; }
    try {
      const st = await stat(LOCK_DIR);
      if (Date.now() - st.mtimeMs > 10 * 60 * 1000) { await rm(LOCK_DIR, { recursive: true, force: true }); continue; }
    } catch {}
    if (waited === 0) console.log('SHOT_LOCK: waiting for another screenshot to finish...');
    await new Promise(r => setTimeout(r, 2500));
    if (waited > 12 * 60 * 1000) { console.log('SHOT_LOCK: giving up after 12min'); lockHeld = false; break; }
  }
}
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const errors = [];
const logs = [];
let browser;
try {
  browser = await puppeteer.launch({
    executablePath: chromeBin,
    headless: true,
    protocolTimeout: timeout,
    args: [
      '--no-sandbox', '--disable-dev-shm-usage', '--no-first-run', '--no-default-browser-check',
      '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl',
      '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
      `--window-size=${width},${height}`,
    ],
    userDataDir: join(ROOT, '.tmp', 'chrome-' + process.pid),
    defaultViewport: { width, height, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  page.on('console', m => {
    const t = m.type();
    if (t === 'error') errors.push(m.text());
    else logs.push('[' + t + '] ' + m.text());
  });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + (e && e.message)));
  const url = `http://127.0.0.1:${port}/${pagePath}` + (params ? ('?' + params) : '');
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout });
  try {
    await page.waitForFunction('window.__READY === true', { timeout, polling: 250 });
  } catch (e) { errors.push('READY_TIMEOUT: ' + e.message); }
  if (evalScript) {
    try { await page.evaluate(`(async () => { ${evalScript} })()`); }
    catch (e) { errors.push('EVAL_ERROR: ' + e.message); }
  }
  // let the render loop settle (clouds/water anim + post FX warmup)
  await page.evaluate(() => new Promise(r => {
    let n = 0; const tick = () => { if (++n >= 12) r(); else requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  })).catch(() => {});
  await new Promise(r => setTimeout(r, waitMs));
  await mkdir(new URL('.', 'file://' + out), { recursive: true }).catch(() => {});
  await page.screenshot({ path: out, type: 'png' });
  const info = await page.evaluate(() => (window.__INFO ? window.__INFO() : null)).catch(() => null);
  console.log('SHOT: ' + out);
  if (info) console.log('INFO: ' + JSON.stringify(info));
  if (errors.length) { console.log('ERRORS(' + errors.length + '):'); errors.slice(0, 25).forEach(e => console.log('  ! ' + e.slice(0, 500))); }
  const warn = logs.filter(l => l.includes('warn')).slice(0, 10);
  if (warn.length) { console.log('WARNS:'); warn.forEach(w => console.log('  ~ ' + w.slice(0, 300))); }
  process.exitCode = 0;
} catch (e) {
  console.error('HARNESS_FAIL:', e && e.stack || e);
  process.exitCode = 1;
} finally {
  try { await browser?.close(); } catch {}
  try { await new Promise(r => server.close(r)); } catch {}
  await rm(join(ROOT, '.tmp', 'chrome-' + process.pid), { recursive: true, force: true }).catch(() => {});
  if (lockHeld) await rm(LOCK_DIR, { recursive: true, force: true }).catch(() => {});
}