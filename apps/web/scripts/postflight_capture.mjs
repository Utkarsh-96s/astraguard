import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const outputDir = path.resolve('C:/Users/REO/.gemini/antigravity-ide/brain/368a21e7-02eb-45fe-b8a7-57336ebc92c2/postflight_screenshots');

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

const routes = [
  '/',
  '/technology',
  '/dashboard',
  '/dashboard/health',
  '/dashboard/debris',
  '/dashboard/disaster',
  '/dashboard/alerts',
  '/dashboard/models',
  '/dashboard/explore',
  '/dashboard/demo'
];

const widths = [
  { width: 1280, height: 800 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
  { width: 2560, height: 1440 },
  { width: 390, height: 844 }
];

const zooms = [1.0, 1.1, 1.25];

async function runPostflight() {
  console.log(`[postflight] Launching Chrome...`);
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const diagnosisData = {
    textOutlines: [],
    pageDimensions: {},
    contrastSummary: [],
    nestedScrollContainers: {}
  };

  for (const { width, height } of widths) {
    for (const zoom of zooms) {
      const zoomPct = Math.round(zoom * 100);
      console.log(`[postflight] Capturing at ${width}x${height} zoom ${zoomPct}%...`);
      
      const context = await browser.newContext({
        viewport: { width, height },
        deviceScaleFactor: 1,
      });

      const page = await context.newPage();

      for (const route of routes) {
        const slug = route === '/' ? 'home' : route.replace(/\//g, '_').slice(1);
        const url = `http://localhost:3000${route}`;
        
        try {
          await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
          
          if (zoom !== 1.0) {
            await page.evaluate((z) => {
              document.body.style.zoom = `${z}`;
            }, zoom);
          }

          await page.waitForTimeout(300);

          const filename = `${slug}_w${width}_z${zoomPct}.png`;
          const filePath = path.join(outputDir, filename);
          await page.screenshot({ path: filePath, fullPage: false });

          // Run diagnostics on 1440px @ 100% zoom
          if (width === 1440 && zoom === 1.0) {
            const pageDiag = await page.evaluate((currentRoute) => {
              const diag = {
                route: currentRoute,
                scrollWidth: document.documentElement.scrollWidth,
                innerWidth: window.innerWidth,
                scrollHeight: document.documentElement.scrollHeight,
                innerHeight: window.innerHeight,
                mainWidth: document.querySelector('main')?.getBoundingClientRect().width || 0,
                mainHeight: document.querySelector('main')?.getBoundingClientRect().height || 0,
                textContainersWithBorders: []
              };

              // Check text containers with borders/outlines/shadows on marketing homepage
              if (currentRoute === '/') {
                const textNodes = document.querySelectorAll('.marketing-scope p, .marketing-scope h1, .marketing-scope h2, .marketing-scope h3, .marketing-scope span:not([role="button"])');
                textNodes.forEach((el) => {
                  const style = window.getComputedStyle(el);
                  const border = parseFloat(style.borderTopWidth) > 0 || parseFloat(style.borderRightWidth) > 0;
                  const shadow = style.boxShadow && style.boxShadow !== 'none';
                  const outline = parseFloat(style.outlineWidth) > 0;
                  if (border || shadow || outline) {
                    diag.textContainersWithBorders.push({
                      tag: el.tagName.toLowerCase(),
                      text: (el.textContent || '').trim().slice(0, 30),
                      border: style.border,
                      shadow: style.boxShadow
                    });
                  }
                });
              }

              return diag;
            }, route);

            diagnosisData.pageDimensions[route] = {
              scrollWidth: pageDiag.scrollWidth,
              innerWidth: pageDiag.innerWidth,
              scrollHeight: pageDiag.scrollHeight,
              innerHeight: pageDiag.innerHeight,
              mainWidth: pageDiag.mainWidth,
              mainWidthRatio: (pageDiag.mainWidth / pageDiag.innerWidth).toFixed(3),
              hasHorizontalOverflow: pageDiag.scrollWidth > pageDiag.innerWidth,
              textContainersWithBorders: pageDiag.textContainersWithBorders
            };
          }
        } catch (err) {
          console.error(`[postflight] Error on ${route} at ${width}x${height} z${zoom}:`, err.message);
        }
      }

      await page.close();
      await context.close();
    }
  }

  await browser.close();

  const diagPath = path.join(outputDir, 'postflight_diagnosis.json');
  fs.writeFileSync(diagPath, JSON.stringify(diagnosisData, null, 2));
  console.log(`[postflight] Completed! Captured all screenshots and diagnosis to ${outputDir}`);
}

runPostflight().catch(console.error);
