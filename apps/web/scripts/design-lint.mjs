import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webRoot = path.resolve(__dirname, '..');

const marketingDir = path.join(webRoot, 'src', 'components', 'marketing');
const marketingPage = path.join(webRoot, 'src', 'app', 'page.tsx');

const filesToLint = [];

if (fs.existsSync(marketingDir)) {
  const dirFiles = fs.readdirSync(marketingDir)
    .filter(f => f.endsWith('.tsx') || f.endsWith('.ts') || f.endsWith('.jsx') || f.endsWith('.js'))
    .map(f => path.join(marketingDir, f));
  filesToLint.push(...dirFiles);
}

if (fs.existsSync(marketingPage)) {
  filesToLint.push(marketingPage);
}

if (filesToLint.length === 0) {
  console.log('No marketing files found to lint yet.');
  process.exit(0);
}

let hasErrors = false;

// Allowed color tokens
const ALLOWED_HEX = new Set([
  '#000000', '#f0f0fa', '#545457', '#404040'
]);

// Check rules
const FORBIDDEN_SHADOW_REGEX = /\b(shadow-(?:sm|md|lg|xl|2xl|inner|glass)|box-shadow|drop-shadow)\b/i;
const FORBIDDEN_GRADIENT_REGEX = /\bbg-gradient-(?:to-[trbl]{1,2})\b/i;
const FORBIDDEN_RADIUS_REGEX = /\brounded-(?:md|lg|xl|2xl|3xl)\b/i;
const FORBIDDEN_TAILWIND_COLORS_REGEX = /\b(text|bg|border)-(?:red|green|blue|yellow|amber|emerald|indigo|purple|pink|cyan|sky|teal|rose|violet|orange)-(?:[0-9]{2,3})\b/i;
const FORBIDDEN_FILLED_BUTTON_REGEX = /<button[^>]*\b(bg-(?:\[#f0f0fa\]|white|slate|gray|zinc|neutral|bone))\b/i;

// Non-interactive marketing components where borders, outlines, rings, and shadows are forbidden
const NON_INTERACTIVE_COMPONENTS = new Set([
  'BodyParagraph.tsx',
  'SectionHeadline.tsx',
  'FullBleedSection.tsx',
  'TelemetryStrip.tsx',
  'MetricsList.tsx',
  'Footer.tsx',
]);

const FORBIDDEN_TEXT_BORDER_REGEX = /<(?:p|h[1-6]|span)[^>]*\b(?:border(?:-[a-z0-9[\]#_-]+)?|ring(?:-[a-z0-9[\]#_-]+)?|outline(?:-[a-z0-9[\]#_-]+)?)\b/i;
const BORDER_OR_FRAME_REGEX = /\b(?:border|border-(?:t|b|l|r|x|y|space-separator|white|neutral|zinc|gray)|ring|outline)\b(?!\s*[:=])/i;

filesToLint.forEach((filePath) => {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const relativePath = path.relative(webRoot, filePath);
  const baseName = path.basename(filePath);

  // 7. Check non-interactive components for borders/outlines/frames
  if (NON_INTERACTIVE_COMPONENTS.has(baseName)) {
    lines.forEach((line, idx) => {
      const lineNum = idx + 1;
      // Skip comments or imports
      if (line.trim().startsWith('//') || line.trim().startsWith('/*') || line.trim().startsWith('*')) return;
      if (line.includes('import ') || line.includes('export interface')) return;
      
      // Focus-visible is allowed on interactive elements only, not in these non-interactive components
      if (BORDER_OR_FRAME_REGEX.test(line)) {
        console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Non-interactive marketing component cannot have borders/rings/outlines: "${line.trim()}"`);
        hasErrors = true;
      }
    });
  }

  // 8. Check text tags across all files
  if (FORBIDDEN_TEXT_BORDER_REGEX.test(content)) {
    lines.forEach((line, idx) => {
      const lineNum = idx + 1;
      if (FORBIDDEN_TEXT_BORDER_REGEX.test(line)) {
        console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Direct border/ring/outline on text element (<p>, <h*>, <span>) is forbidden: "${line.trim()}"`);
        hasErrors = true;
      }
    });
  }

  lines.forEach((line, idx) => {
    const lineNum = idx + 1;

    // 1. Check shadows
    if (FORBIDDEN_SHADOW_REGEX.test(line)) {
      console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Box shadow is forbidden on homepage: "${line.trim()}"`);
      hasErrors = true;
    }

    // 2. Check forbidden gradients (exclude mask-image)
    if (FORBIDDEN_GRADIENT_REGEX.test(line)) {
      console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Background gradient is forbidden on homepage: "${line.trim()}"`);
      hasErrors = true;
    }

    // 3. Check border-radius > 4px (rounded-full is allowed for pill selector, rounded/rounded-sm allowed for 4px/2px)
    if (FORBIDDEN_RADIUS_REGEX.test(line)) {
      console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Border radius > 4px is forbidden (use rounded or rounded-sm, or rounded-full for pills): "${line.trim()}"`);
      hasErrors = true;
    }

    // 4. Check chromatic Tailwind colors
    if (FORBIDDEN_TAILWIND_COLORS_REGEX.test(line)) {
      console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Chromatic Tailwind color forbidden on homepage: "${line.trim()}"`);
      hasErrors = true;
    }

    // 5. Check filled button
    if (FORBIDDEN_FILLED_BUTTON_REGEX.test(line)) {
      console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Filled button forbidden (buttons must be 1px ghost outlines): "${line.trim()}"`);
      hasErrors = true;
    }

    // 6. Check hex colors (ignore href="#..." anchor links)
    const cleanLine = line.replace(/href=["']#[a-zA-Z0-9_-]+["']/g, '');
    const hexMatches = cleanLine.match(/#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-zA-Z0-9_-])/g);
    if (hexMatches) {
      hexMatches.forEach((hex) => {
        const lower = hex.toLowerCase();
        const fullHex = lower.length === 4 ? `#${lower[1]}${lower[1]}${lower[2]}${lower[2]}${lower[3]}${lower[3]}` : lower;
        if (!ALLOWED_HEX.has(fullHex)) {
          console.error(`[design:lint] Error at ${relativePath}:${lineNum} - Hex color "${hex}" not allowed. Only #000000, #f0f0fa, #545457, #404040 are permitted.`);
          hasErrors = true;
        }
      });
    }
  });
});

if (hasErrors) {
  console.error('\n[design:lint] FAILED: Design system violations detected.');
  process.exit(1);
} else {
  console.log(`[design:lint] PASSED: All ${filesToLint.length} marketing files adhere to docs/design.md rules.`);
}
