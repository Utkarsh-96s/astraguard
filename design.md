# Design System — SpaceX Cinematic Style Reference

> Single Source of Truth for the ASTRA-GUARD Marketing Homepage. Strictly monochrome, full-bleed photography, typographic dominance, zero decoration.

---

## 1. Core Philosophy

The homepage operates in the visual register of high-aerospace engineering (SpaceX style):
- **Canvas:** Pitch-black `#000000` void canvas everywhere.
- **Monochrome Only:** No accent or chromatic colors anywhere on the homepage. Foreground `#f0f0fa` only, secondary `#545457`, separators `#404040`.
- **Text Directly on Canvas/Photos:** No cards, no frosted glass, no panels, no tinted background boxes behind text. Text floats directly on photography or solid black.
- **Full-Bleed Photography:** Full-viewport photography sections with a uniform subtle dim overlay (max `rgba(0,0,0,0.35)`) and vertical edge mask fading into pure `#000000`.
- **Ghost Linearity:** Every interactive element uses a 1px hairline outline (`#f0f0fa`), transparent background, and 4px border radius. Never filled buttons.

---

## 2. Color Tokens

| Name | Hex Value | CSS Variable | Role |
|---|---|---|---|
| Canvas Black | `#000000` | `--color-space-canvas` | Base page background across all sections |
| Foreground White | `#f0f0fa` | `--color-space-fg` | Primary display headlines, active links, primary ghost button outlines/text |
| Secondary Gray | `#545457` | `--color-space-secondary` | Body paragraphs, secondary button outlines/text, muted metadata |
| Separator Iron | `#404040` | `--color-space-separator` | Hairline dividers, subtle borders, telemetry delimiters |

> [!IMPORTANT]
> **Zero Chromatic Color Rule:** No red, green, blue, amber, cyan, or purple is permitted on the homepage. Risk levels appear as plain uppercase text strings (`NOMINAL`, `WATCH`, `WARNING`, `CRITICAL`), never colored badges.

---

## 3. Typography Scale & Fonts

Primary Typeface: **Barlow** (via `next/font/google`, weights 400 and 700), exposed as `--font-d-din` and `--font-d-din-bold`.

- **Headlines:**
  - Size: `48px` (responsive clamp: `clamp(30px, 4vw, 48px)` on mobile)
  - Weight: Bold (`700`)
  - Case: `UPPERCASE`
  - Letter-spacing: `0.02em` (`tracking-wider`)
  - Line-height: `1.0` to `1.25`
  - Font: `var(--font-d-din-bold)`
- **Body Copy:**
  - Size: `13px`
  - Weight: Normal (`400`)
  - Case: Sentence case
  - Letter-spacing: `0.10em`
  - Line-height: `1.7`
  - Width limit: `max-width: 450px - 500px`
  - Color: `#545457`
  - Font: `var(--font-d-din)`
- **Nav, Section Labels, Buttons & Metadata:**
  - Size: `10px - 13px`
  - Weight: Bold (`700`)
  - Case: `UPPERCASE`
  - Letter-spacing: `0.09em - 0.10em`
  - Numbers: `font-feature-settings: "tnum"` (tabular numerals)

---

## 4. Interactive Elements & Buttons

All buttons are un-tinted ghost outlines:
- **Primary Ghost Button:**
  - Border: `1px solid #f0f0fa`
  - Fill: `transparent`
  - Text: `#f0f0fa`, 11px-12px, 700, uppercase, tracking `0.10em`
  - Border radius: `4px`
  - Hover / Focus: subtle background fill `rgba(240, 240, 250, 0.08)`, border opacity change. No shadows, no glows, no chromatic color.
- **Secondary Ghost Button:**
  - Border: `1px solid #545457`
  - Fill: `transparent`
  - Text: `#545457`, 11px-12px, 700, uppercase, tracking `0.10em`
  - Border radius: `4px`
  - Hover / Focus: border color `#f0f0fa`, text `#f0f0fa`, subtle fill `rgba(240, 240, 250, 0.04)`.
- **Pill Button (Compact Toggles / Selectors):**
  - Border: `1px solid #f0f0fa`
  - Border radius: `32px` (strictly reserved for compact toggles & selector chips).

---

## 5. Section Layout & Rhythm

- **Single-Column Full-Bleed:**
  - Each section has `min-height: 100vh`, relative positioning, `w-full overflow-hidden`.
  - Background: Full-cover photograph using `next/image` with `sizes="100vw"`, `object-fit: cover`.
  - Photo Overlay: Uniform dim overlay `rgba(0, 0, 0, 0.35)` + vertical gradient mask fading top and bottom edges into pure `#000000`.
- **Text Block Placement:**
  - Left-aligned in the left third of the screen (`30% - 35%` container width, `max-width: 500px`).
  - Vertically centered within the viewport.
  - Section vertical rhythm: `60px`; internal element gap: `18px`.
  - Mobile (<= 768px): text block spans full width with `20px` side padding, anchored in the lower-left quadrant.

---

## 6. Navigation Bar

- Fixed or absolute top bar, completely transparent (`bg-transparent`), zero backdrop blur.
- Remains identical in visual appearance on scroll (no frosted glass shift).
- Left: Wordmark `ASTRA-GUARD` in 14px bold caps (`#f0f0fa`).
- Center / Right: Anchor links (`MISSION`, `HEALTH`, `DEBRIS`, `EARTH`, `ENGINE`, `DEMO`, `TEAM`) in 11px tracked bold caps (`#f0f0fa`).
- Far Right:
  - Scenario Selector widget (1px outline, caret, label `SCENARIO`) listing scenarios from `GET /api/v1/demo/scenarios`.
  - Ghost CTA button: `LAUNCH DASHBOARD` -> `/dashboard`.
- Mobile: Ghost `MENU` button opening a full-screen `#000000` overlay.

---

## 7. Motion & Transitions

- Minimal opacity fade-in (`300ms - 400ms`) as sections enter viewport.
- Zero parallax, zero scale transforms, zero glowing neon.
- Fully disabled when `prefers-reduced-motion` is active.

---

## 8. Quick Start CSS Tokens

```css
:root {
  --color-space-canvas: #000000;
  --color-space-fg: #f0f0fa;
  --color-space-secondary: #545457;
  --color-space-separator: #404040;
  --font-d-din: var(--font-barlow), sans-serif;
  --font-d-din-bold: var(--font-barlow), sans-serif;
}
```
