#!/usr/bin/env node
/**
 * ASTRA-GUARD Figure & Honesty Audit Runner
 * Delegates to scripts/honesty_audit.py from the repository root.
 */
import { spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..', '..', '..');
const auditScript = path.join(rootDir, 'scripts', 'honesty_audit.py');

console.log('[audit:figures] Running ASTRA-GUARD cryptographic honesty & figure audit...');
const result = spawnSync('python', [auditScript], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true,
});

if (result.status !== 0) {
  console.error(`[audit:figures] FAILED with exit code ${result.status}`);
  process.exit(result.status || 1);
} else {
  console.log('[audit:figures] PASSED: All figures, models, benchmarks, and frontend references verified.');
}
