import { chromium } from 'playwright-core';
import { serve } from './serve.mjs';
const server = await serve(process.cwd());
const port = server.address().port;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 400 } });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[err]', e.message));
for (const mode of ['tex', 'clay']) {
  await page.goto(`http://127.0.0.1:${port}/inspect.html?mode=${mode}`);
  await page.waitForFunction('window.done === true', null, { timeout: 120000 });
  await page.locator('#c').screenshot({ path: `${process.argv[2]}/inspect_${mode}.png` });
}
await browser.close(); server.close();
