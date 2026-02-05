# SIGMAX SDK - Installation & Testing Guide

This guide will help you build, test, and use the SIGMAX TypeScript SDK.

## Prerequisites

Before you begin, ensure you have:

- Node.js 18.0.0 or higher
- npm, yarn, or pnpm package manager
- SIGMAX API server running (default: http://localhost:8000)
- SIGMAX API key

## Installation Options

If `@sigmax/sdk` is published, you can install directly:

```bash
npm install @sigmax/sdk
# yarn add @sigmax/sdk
# pnpm add @sigmax/sdk
```

If not published, install from source:

## Step 1: Install Dependencies

Navigate to the SDK directory and install dependencies:

```bash
cd /Users/mac/Projects/SIGMAX/sdk/typescript
npm install
```

This will install:
- `typescript` - TypeScript compiler

## Step 2: Build the SDK

Build the SDK to generate CommonJS, ESM, and TypeScript definitions:

```bash
npm run build
```

This will:
1. Clean previous builds (`npm run clean`)
2. Build CommonJS version (`npm run build:cjs`)
3. Build ESM version (`npm run build:esm`)
4. Generate TypeScript definitions (`npm run build:types`)
5. Finalize the build (`npm run build:finalize`)

**Expected output in `dist/` directory:**
```
dist/
├── index.js          # CommonJS entry point
├── index.mjs         # ESM entry point
├── index.d.ts        # TypeScript definitions
├── types.d.ts
├── client.d.ts
├── errors.d.ts
├── client.js
├── types.js
├── errors.js
└── utils/
    ├── fetch.js
    ├── fetch.d.ts
    ├── sse.js
    └── sse.d.ts
```

## Step 3: Test the SDK Locally

### Option A: Test with Examples

Set your API key as an environment variable:

```bash
export SIGMAX_API_KEY="your-api-key-here"
export SIGMAX_API_URL="http://localhost:8000"
```

Run the Node.js example:

```bash
npm run example:basic
```

This will run `examples/node-example.js` which demonstrates:
- Health check
- Symbol analysis
- Portfolio retrieval
- Agent debate

### Option B: Test with npm link

Link the SDK locally so you can use it in other projects:

```bash
# In the SDK directory
npm link

# In your test project directory
cd /path/to/your/test/project
npm link @sigmax/sdk
```

Then use it in your test project:

```typescript
import { SigmaxClient } from '@sigmax/sdk';

const client = new SigmaxClient({
  apiKey: process.env.SIGMAX_API_KEY!,
  apiUrl: 'http://localhost:8000'
});

const result = await client.healthCheck();
console.log(result);
```

### Option C: Test Streaming Example

For the streaming example (requires `tsx`):

```bash
# Install tsx globally or use npx
npm run example:streaming
# or
npx tsx examples/streaming.ts
```

## Step 4: Test in Browser

1. Build the SDK first (if not already done):
   ```bash
   npm run build
   ```

2. Open the browser example:
   ```bash
   # Serve the directory
   npx serve .
   ```

3. Navigate to `http://localhost:3000/examples/browser-example.html`

4. Enter your API key and test the various functions

## Step 5: Verify Build Output

Check that all required files exist:

```bash
ls -la dist/
```

You should see:
- `index.js` (CommonJS)
- `index.mjs` (ESM)
- `index.d.ts` (TypeScript definitions)
- Supporting files (`client.js`, `types.js`, `errors.js`, etc.)

Test imports:

```bash
# Test CommonJS
node -e "const { SigmaxClient } = require('./dist/index.js'); console.log(SigmaxClient.name);"

# Test ESM
node --input-type=module -e "import { SigmaxClient } from './dist/index.mjs'; console.log(SigmaxClient.name);"
```

## Step 6: Verify TypeScript Definitions

Create a test TypeScript file:

```typescript
// test.ts
import { SigmaxClient, AnalysisResult } from '@sigmax/sdk';

const client = new SigmaxClient({
  apiKey: 'test',
  apiUrl: 'http://localhost:8000'
});

async function test() {
  const result: AnalysisResult = await client.analyze('BTC/USDT');
  console.log(result.decision?.action);
}
```

Check for TypeScript errors:

```bash
npx tsc --noEmit test.ts
```

## Troubleshooting

### Build Fails

If the build fails, try:

```bash
# Clean and rebuild
npm run clean
npm install
npm run build
```

### Examples Don't Run

Make sure:
1. SIGMAX API server is running on `http://localhost:8000`
2. API key is set in environment variables
3. Dependencies are installed (`npm install`)

### TypeScript Errors

Ensure you have TypeScript 5.0+ installed:

```bash
npx tsc --version
```

If not, upgrade:

```bash
npm install -D typescript@latest
```

### Import Errors

Make sure you're importing from the correct location:

- In your project: `import { SigmaxClient } from '@sigmax/sdk';`
- When testing locally with npm link: Same as above
- When importing built files directly: `import { SigmaxClient } from './dist/index.mjs';`

## Publishing to npm (Optional)

When ready to publish:

1. Update version in `package.json`
2. Update `CHANGELOG.md`
3. Build the package:
   ```bash
   npm run build
   ```

4. Test the package:
   ```bash
   npm pack
   # This creates a .tgz file
   ```

5. Publish:
   ```bash
   npm publish
   ```

## Development Workflow

For active development:

```bash
# Watch mode - rebuilds on file changes
npm run dev

# In another terminal, test your changes
npm run example:basic
```

## Environment Setup

Create a `.env` file in your project:

```bash
# .env
SIGMAX_API_KEY=your-api-key-here
SIGMAX_API_URL=http://localhost:8000
```

Load it in Node.js:

```typescript
import dotenv from 'dotenv';
dotenv.config();

const client = new SigmaxClient({
  apiKey: process.env.SIGMAX_API_KEY!,
  apiUrl: process.env.SIGMAX_API_URL
});
```

## Verification Checklist

Before using the SDK, verify:

- [ ] Dependencies installed (`node_modules/` exists)
- [ ] Build completed successfully (`dist/` directory exists)
- [ ] `dist/index.js` exists (CommonJS)
- [ ] `dist/index.mjs` exists (ESM)
- [ ] `dist/index.d.ts` exists (TypeScript definitions)
- [ ] Examples run without errors
- [ ] SIGMAX API server is accessible
- [ ] API key is valid

## Next Steps

Once the SDK is built and tested:

1. Read [QUICKSTART.md](./QUICKSTART.md) for usage examples
2. Explore [examples/](./examples) for more use cases
3. Check [README.md](./README.md) for complete API reference
4. Start building your trading application!

## Support

If you encounter issues:

1. Check this installation guide
2. Review the troubleshooting section
3. Check SIGMAX API server logs
4. Verify Node.js and npm versions
5. Try cleaning and rebuilding (`npm run clean && npm run build`)

## System Requirements

- **Node.js**: 18.0.0 or higher
- **TypeScript**: 5.0.0 or higher (dev dependency)
- **Browsers**: Modern browsers with ES2020+ support
- **SIGMAX API**: Version 2.0.0 or compatible

---

**Installation Guide Version:** 1.0.0
**Last Updated:** 2024-12-21
