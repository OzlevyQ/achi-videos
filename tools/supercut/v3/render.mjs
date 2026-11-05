// node render.mjs page.html out.mp4 seconds [query] [fps]
import { createRequire } from 'module';
import { spawn } from 'child_process';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/ozlevy/Projects/whats-mac/server/node_modules/playwright-core');
const [, , page_, out, secs, query = '', fpsArg = '30'] = process.argv;
const fps = Number(fpsArg), N = Math.round(Number(secs) * fps);
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', args: ['--allow-file-access-from-files', '--hide-scrollbars', '--force-device-scale-factor=1'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => console.error('PAGEERR', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
await page.goto('file://' + page_ + (query ? '?' + query : ''));
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => window.ready || Promise.resolve());
const ff = spawn('/usr/local/bin/ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
for (let i = 0; i < N; i++) {
  await page.evaluate(t => window.seek(t), i / fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('rendered', out, N, 'frames');
