# TypeScript SDK Release Process

## Overview

This SDK is published via GitHub Actions when a tag matching `sdk-ts-v*` is pushed.

## Prerequisites

- GitHub secret `NPM_TOKEN` with publish rights to `@sigmax` scope
- `sdk/typescript/package.json` version updated

## Release Steps

1. Update the version:

```bash
cd sdk/typescript
npm version 1.0.1
```

2. Commit the version bump:

```bash
git add package.json package-lock.json

git commit -m "chore(sdk): release v1.0.1"
```

3. Tag and push:

```bash
git tag sdk-ts-v1.0.1

git push origin main --tags
```

4. GitHub Actions will build and publish automatically.

## Notes

- If you need a prerelease, use a `-beta` version and tag it (e.g., `sdk-ts-v1.0.2-beta.1`).
- Verify publish status with:

```bash
npm view @sigmax/sdk version
```
