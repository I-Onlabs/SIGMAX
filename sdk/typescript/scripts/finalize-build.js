#!/usr/bin/env node
/**
 * Finalize build - Copy and rename files for dual package support
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 Finalizing build...');

const distDir = path.join(__dirname, '..', 'dist');

// Copy CJS index to dist/index.js
const cjsIndexPath = path.join(distDir, 'cjs', 'index.js');
const distIndexPath = path.join(distDir, 'index.js');

if (fs.existsSync(cjsIndexPath)) {
  fs.copyFileSync(cjsIndexPath, distIndexPath);
  console.log('✓ Copied CJS index.js');
}

// Copy ESM index to dist/index.mjs
const esmIndexPath = path.join(distDir, 'esm', 'index.js');
const distMjsPath = path.join(distDir, 'index.mjs');

if (fs.existsSync(esmIndexPath)) {
  fs.copyFileSync(esmIndexPath, distMjsPath);
  console.log('✓ Copied ESM index.mjs');
}

// Copy all other CJS files to dist root (for imports to work)
const cjsDir = path.join(distDir, 'cjs');
if (fs.existsSync(cjsDir)) {
  copyRecursive(cjsDir, distDir, ['index.js']);
  console.log('✓ Copied supporting files');
}

// Clean up cjs and esm directories
if (fs.existsSync(path.join(distDir, 'cjs'))) {
  fs.rmSync(path.join(distDir, 'cjs'), { recursive: true });
}
if (fs.existsSync(path.join(distDir, 'esm'))) {
  fs.rmSync(path.join(distDir, 'esm'), { recursive: true });
}

console.log('✅ Build finalized!');

/**
 * Recursively copy directory
 */
function copyRecursive(src, dest, exclude = []) {
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (exclude.includes(entry.name)) {
      continue;
    }

    if (entry.isDirectory()) {
      if (!fs.existsSync(destPath)) {
        fs.mkdirSync(destPath, { recursive: true });
      }
      copyRecursive(srcPath, destPath);
    } else {
      if (!fs.existsSync(destPath)) {
        fs.copyFileSync(srcPath, destPath);
      }
    }
  }
}
