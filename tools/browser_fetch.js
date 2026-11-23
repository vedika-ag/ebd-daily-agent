// Load one page in headless Chromium and print its final HTML to stdout.
// Used by tools/fetch.py as a fallback for pages that need JavaScript.
// Usage: node tools/browser_fetch.js URL
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  if (!url) { console.error('usage: node tools/browser_fetch.js URL'); process.exit(2); }
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  const browser = await chromium.launch(proxy ? { proxy: { server: proxy } } : {});
  try {
    const page = await browser.newPage();
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);
    process.stderr.write(`HTTP ${resp ? resp.status() : 0}\n`);
    process.stdout.write(await page.content());
  } catch (e) {
    console.error(String(e).slice(0, 300));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
