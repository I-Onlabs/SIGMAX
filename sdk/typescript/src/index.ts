/**
 * SIGMAX TypeScript SDK
 *
 * Production-ready SDK for the SIGMAX autonomous AI crypto trading system
 *
 * @packageDocumentation
 */

// Export main client
export { SigmaxClient } from './client';

// Export all types
export * from './types';

// Export errors
export * from './errors';

// Export utilities (for advanced usage)
export { buildUrl } from './utils/fetch';
export { streamSSE } from './utils/sse';
