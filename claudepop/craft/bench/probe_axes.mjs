import puppeteer from 'puppeteer-core'; import { pathToFileURL } from 'node:url';
const b = await puppeteer.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true, args: ['--allow-file-access-from-files', '--no-sandbox', '--disable-accelerated-2d-canvas', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage(); await p.goto(pathToFileURL(process.cwd() + '/probe_axes.html').href); console.log(JSON.stringify(await p.evaluate(() => window.probe()), null, 1)); await b.close();
