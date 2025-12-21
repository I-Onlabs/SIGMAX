/**
 * SIGMAX TypeScript SDK - Server-Sent Events (SSE) Utilities
 */

import { StreamEvent } from '../types';
import { NetworkError, TimeoutError } from '../errors';

export interface SSEOptions {
  headers?: Record<string, string>;
  timeout?: number;
  signal?: AbortSignal;
  onOpen?: () => void;
  onError?: (error: Error) => void;
}

/**
 * Stream Server-Sent Events using async iterator pattern
 *
 * Works in both Node.js and browser environments
 */
export async function* streamSSE(
  url: string,
  options: SSEOptions = {}
): AsyncIterableIterator<StreamEvent> {
  const { headers = {}, timeout = 300000, signal, onOpen, onError } = options;

  // Detect environment
  const isNode = typeof process !== 'undefined' && process.versions?.node;

  if (isNode) {
    // Node.js implementation
    yield* streamSSENode(url, { headers, timeout, signal, onOpen, onError });
  } else {
    // Browser implementation
    yield* streamSSEBrowser(url, { headers, timeout, signal, onOpen, onError });
  }
}

/**
 * Browser SSE implementation using EventSource API
 */
async function* streamSSEBrowser(
  url: string,
  options: SSEOptions
): AsyncIterableIterator<StreamEvent> {
  const { headers = {}, timeout, signal, onOpen, onError } = options;

  // EventSource doesn't support custom headers directly,
  // so we need to use fetch with streaming
  const controller = new AbortController();
  const timeoutId = timeout ? setTimeout(() => controller.abort(), timeout) : null;

  const fetchSignal = signal
    ? createMergedSignal(signal, controller.signal)
    : controller.signal;

  try {
    const response = await fetch(url, {
      headers: {
        Accept: 'text/event-stream',
        ...headers,
      },
      signal: fetchSignal,
    });

    if (!response.ok) {
      throw new NetworkError(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new NetworkError('Response body is null');
    }

    onOpen?.();

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Process complete events
        const events = parseSSEBuffer(buffer);
        for (const event of events.events) {
          yield event;
        }
        buffer = events.remaining;
      }
    } finally {
      reader.releaseLock();
      if (timeoutId) clearTimeout(timeoutId);
    }
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      const timeoutError = new TimeoutError(timeout || 0);
      onError?.(timeoutError);
      throw timeoutError;
    }

    onError?.(error);
    throw error;
  }
}

/**
 * Node.js SSE implementation using fetch with stream processing
 */
async function* streamSSENode(
  url: string,
  options: SSEOptions
): AsyncIterableIterator<StreamEvent> {
  const { headers = {}, timeout, signal, onOpen, onError } = options;

  const controller = new AbortController();
  const timeoutId = timeout ? setTimeout(() => controller.abort(), timeout) : null;

  const fetchSignal = signal
    ? createMergedSignal(signal, controller.signal)
    : controller.signal;

  try {
    const response = await fetch(url, {
      headers: {
        Accept: 'text/event-stream',
        ...headers,
      },
      signal: fetchSignal,
    });

    if (!response.ok) {
      throw new NetworkError(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new NetworkError('Response body is null');
    }

    onOpen?.();

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      // Type assertion for Node.js ReadableStream
      const nodeStream = response.body as any;

      for await (const chunk of nodeStream) {
        buffer += decoder.decode(chunk, { stream: true });

        // Process complete events
        const events = parseSSEBuffer(buffer);
        for (const event of events.events) {
          yield event;
        }
        buffer = events.remaining;
      }
    } finally {
      if (timeoutId) clearTimeout(timeoutId);
    }
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      const timeoutError = new TimeoutError(timeout || 0);
      onError?.(timeoutError);
      throw timeoutError;
    }

    onError?.(error);
    throw error;
  }
}

/**
 * Parse SSE buffer and extract complete events
 */
function parseSSEBuffer(buffer: string): {
  events: StreamEvent[];
  remaining: string;
} {
  const events: StreamEvent[] = [];
  const lines = buffer.split('\n');
  let i = 0;

  while (i < lines.length) {
    // Look for event lines
    if (lines[i].startsWith('event:')) {
      const eventType = lines[i].substring(6).trim();
      i++;

      // Look for data line
      if (i < lines.length && lines[i].startsWith('data:')) {
        const dataStr = lines[i].substring(5).trim();
        i++;

        // Parse data as JSON
        try {
          const data = JSON.parse(dataStr);
          events.push({
            type: eventType as any,
            ...data,
          });
        } catch {
          // Skip invalid JSON
        }

        // Skip empty line after event
        if (i < lines.length && lines[i] === '') {
          i++;
        }
      }
    } else {
      i++;
    }
  }

  // Remaining buffer (incomplete event)
  const remaining = i < lines.length ? lines.slice(i).join('\n') : '';

  return { events, remaining };
}

/**
 * Create a merged abort signal from multiple signals
 */
function createMergedSignal(...signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();

  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort();
      break;
    }

    signal.addEventListener('abort', () => controller.abort(), { once: true });
  }

  return controller.signal;
}
