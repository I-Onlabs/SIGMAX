#!/bin/bash
set -e

echo "🔨 Building SIGMAX TypeScript SDK..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/

# Create dist directory
mkdir -p dist

# Build CommonJS
echo "📦 Building CommonJS..."
npx tsc --module commonjs --outDir dist/cjs --declaration false
if [ -f "dist/cjs/index.js" ]; then
  cp dist/cjs/index.js dist/index.js
  cp -r dist/cjs/utils dist/
  cp -r dist/cjs/client.js dist/
  cp -r dist/cjs/types.js dist/
  cp -r dist/cjs/errors.js dist/
fi
rm -rf dist/cjs

# Build ESM
echo "📦 Building ESM..."
npx tsc --module esnext --outDir dist/esm --declaration false
if [ -f "dist/esm/index.js" ]; then
  cp dist/esm/index.js dist/index.mjs
  # Note: utils, client, types, errors are shared from CJS build
fi
rm -rf dist/esm

# Build TypeScript declarations
echo "📝 Building TypeScript declarations..."
npx tsc --declaration --emitDeclarationOnly --outDir dist

echo "✅ Build complete!"
echo ""
echo "Output:"
echo "  - dist/index.js (CommonJS)"
echo "  - dist/index.mjs (ESM)"
echo "  - dist/index.d.ts (TypeScript)"
echo "  - dist/types.d.ts"
echo "  - dist/client.d.ts"
echo "  - dist/errors.d.ts"
