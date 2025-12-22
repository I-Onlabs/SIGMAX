import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/**/*.ts'],
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.test.ts',
        'src/**/*.spec.ts',
        'src/utils/**',  // Exclude utils from coverage thresholds (mocked in tests)
        'src/types.ts',  // Type definitions
        'examples/**',
        'scripts/**',
      ],
      thresholds: {
        lines: 45,
        functions: 80,
        branches: 30,
        statements: 45,
      },
    },
  },
});
