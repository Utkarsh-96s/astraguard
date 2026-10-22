import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const outputDir = path.resolve('C:/Users/REO/.gemini/antigravity-ide/brain/368a21e7-02eb-45fe-b8a7-57336ebc92c2/preflight_screenshots');

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

async function runPreflight() {
  console.log(`[preflight] Launching Chrome...`);
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const diagnosisData = {
    textOutlines: [],
    pageDimensions: {},
    contrastIssues: [],
    nestedScrollContainers: {}
  };

  for (const { width, height } of widths) {
    for (const zoom of zooms) {
      const zoomPct = Math.round(zoom * 100);
      console.log(`[preflight] Capturing at ${width}x${height} zoom ${zoomPct}%...`);
      
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
          
          // Apply browser zoom if != 1.0 via CSS zoom or CDP
          if (zoom !== 1.0) {
            await page.evaluate((z) => {
              document.body.style.zoom = `${z}`;
            }, zoom);
          }

          await page.waitForTimeout(400);

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
                bodyHeight: document.body.scrollHeight,
                mainHeight: document.querySelector('main')?.getBoundingClientRect().height || 0,
                nestedScrolls: [],
                textContainersWithBorders: []
              };

              // Check nested scroll containers
              const allElements = document.querySelectorAll('*');
              allElements.forEach((el) => {
                const style = window.getComputedStyle(el);
                const hasScroll = (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
                if (hasScroll && el !== document.documentElement && el !== document.body) {
                  diag.nestedScrolls.push({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    className: (el.className || '').toString().slice(0, 60),
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight
                  });
                }

                // Check text containers with borders/outlines/shadows
                // Exclude buttons, selects, inputs, scenarios, etc.
                const isInteractive = ['BUTTON', 'A', 'INPUT', 'SELECT', 'OPTION'].includes(el.tagName) ||
                  el.getAttribute('role') === 'button' ||
                  el.closest('button') || el.closest('a');
                
                const hasText = el.childNodes.length === 1 && el.childNodes[0].nodeType === 3 && el.textContent.trim().length > 0;
                const isTextTag = ['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'SPAN'].includes(el.tagName);

                if (!isInteractive && (hasText || isTextTag)) {
                  const border = parseFloat(style.borderTopWidth) > 0 || parseFloat(style.borderRightWidth) > 0 ||
                    parseFloat(style.borderBottomWidth) > 0 || parseFloat(style.borderLeftWidth) > 0;
                  const outline = parseFloat(style.outlineWidth) > 0;
                  const shadow = style.boxShadow && style.boxShadow !== 'none';
                  const bg = style.backgroundColor;

                  if (border || outline || shadow) {
                    diag.textContainersWithBorders.push({
                      tag: el.tagName.toLowerCase(),
                      textSnippet: (el.textContent || '').trim().slice(0, 40),
                      className: (el.className || '').toString().slice(0, 80),
                      border: style.border,
                      outline: style.outline,
                      shadow: style.boxShadow
                    });
                  }
                }
              });

              return diag;
            }, route);

            diagnosisData.pageDimensions[route] = {
              scrollWidth: pageDiag.scrollWidth,
              innerWidth: pageDiag.innerWidth,
              scrollHeight: pageDiag.scrollHeight,
              innerHeight: pageDiag.innerHeight,
              mainHeight: pageDiag.mainHeight,
              hasHorizontalOverflow: pageDiag.scrollWidth > pageDiag.innerWidth
            };

            if (pageDiag.nestedScrolls.length > 0) {
              diagnosisData.nestedScrollContainers[route] = pageDiag.nestedScrolls;
            }

            if (pageDiag.textContainersWithBorders.length > 0) {
              diagnosisData.textOutlines.push(...pageDiag.textContainersWithBorders.map(b => ({ ...b, route })));
            }
          }
        } catch (err) {
          console.error(`[preflight] Error on ${route} at ${width}x${height} z${zoom}:`, err.message);
        }
      }

      await page.close();
      await context.close();
    }
  }

  await browser.close();

  // Save diagnostic json
  const diagPath = path.join(outputDir, 'preflight_diagnosis.json');
  fs.writeFileSync(diagPath, JSON.stringify(diagnosisData, null, 2));
  console.log(`[preflight] Completed! Screenshots and diagnosis written to ${outputDir}`);
}

runPreflight().catch(console.error);
