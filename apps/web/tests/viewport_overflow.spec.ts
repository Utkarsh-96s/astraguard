import { test, expect } from "@playwright/test";

const ROUTES = [
  "/",
  "/dashboard",
  "/dashboard/debris",
  "/dashboard/disaster",
  "/dashboard/alerts",
  "/dashboard/models",
  "/dashboard/simulation",
  "/dashboard/explore",
  "/dashboard/demo",
  "/technology",
];

const WIDTHS = [1280, 1440, 1920, 2560, 390];
const ZOOMS = [1.0, 1.1, 1.25];

for (const route of ROUTES) {
  test.describe(`Route: ${route} viewport scaling & overflow`, () => {
    for (const width of WIDTHS) {
      for (const zoom of ZOOMS) {
        test(`w=${width}px zoom=${Math.round(zoom * 100)}% fills viewport with zero overflow`, async ({ page }) => {
          await page.setViewportSize({ width, height: 900 });
          await page.goto(route, { waitUntil: "domcontentloaded", timeout: 30000 });
          await page.waitForTimeout(500);

          if (zoom !== 1.0) {
            await page.evaluate((z) => {
              (document.body.style as any).zoom = `${z}`;
            }, zoom);
            await page.waitForTimeout(200);
          }

          // 1. Assert zero horizontal overflow: scrollWidth <= innerWidth
          const { scrollWidth, innerWidth } = await page.evaluate(() => ({
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth,
          }));

          // Allow at most 1.5px tolerance for sub-pixel rounding across zoom factors
          expect(scrollWidth).toBeLessThanOrEqual(innerWidth + 1.5);

          // 2. For non-home routes on >= 1440px displays, assert main fills >= 90% of innerWidth
          if (route !== "/" && width >= 1440 && zoom === 1.0) {
            const mainWidth = await page.evaluate(() => {
              const main = document.querySelector("main");
              return main ? main.getBoundingClientRect().width : null;
            });

            if (mainWidth !== null) {
              const ratio = mainWidth / innerWidth;
              expect(ratio).toBeGreaterThanOrEqual(0.90);
            }
          }
        });
      }
    }
  });
}
