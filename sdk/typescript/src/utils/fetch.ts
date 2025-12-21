/**
 * SIGMAX TypeScript SDK - Fetch Utilities
 */

import {
  AuthenticationError,
  NetworkError,
  NotFoundError,
  PermissionError,
  RateLimitError,
  ServiceUnavailableError,
  TimeoutError,
  ValidationError,
} from '../errors';

export interface FetchOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  headers?: Record<string, string>;
  timeout?: number;
  signal?: AbortSignal;
}

/**
 * Make an HTTP request with proper error handling
 */
export async function makeRequest<T>(
  url: string,
  options: FetchOptions = {}
): Promise<T> {
  const { method = 'GET', body, headers = {}, timeout = 30000, signal } = options;

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // Merge abort signals if both provided
  const fetchSignal = signal
    ? createMergedSignal(signal, controller.signal)
    : controller.signal;

  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: fetchSignal,
    });

    clearTimeout(timeoutId);

    // Handle HTTP errors
    if (!response.ok) {
      await handleHttpError(response);
    }

    // Parse JSON response
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    // Return empty object for non-JSON responses
    return {} as T;
  } catch (error: any) {
    clearTimeout(timeoutId);

    // Handle abort/timeout
    if (error.name === 'AbortError') {
      throw new TimeoutError(timeout);
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new NetworkError('Network request failed. Please check your connection.');
    }

    // Re-throw our custom errors
    if (
      error instanceof AuthenticationError ||
      error instanceof RateLimitError ||
      error instanceof ValidationError ||
      error instanceof NotFoundError ||
      error instanceof PermissionError ||
      error instanceof ServiceUnavailableError
    ) {
      throw error;
    }

    // Generic network error
    throw new NetworkError(error.message || 'Unknown network error');
  }
}

/**
 * Handle HTTP error responses
 */
async function handleHttpError(response: Response): Promise<never> {
  let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
  let errorDetail: any;

  // Try to parse error body
  try {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      errorDetail = await response.json();
      if (errorDetail.detail) {
        errorMessage = errorDetail.detail;
      }
    }
  } catch {
    // Ignore parse errors
  }

  // Map status codes to error types
  switch (response.status) {
    case 400:
      throw new ValidationError(errorMessage);

    case 401:
      throw new AuthenticationError(errorMessage);

    case 403:
      throw new PermissionError(errorMessage);

    case 404:
      throw new NotFoundError(errorMessage);

    case 429:
      const retryAfter = response.headers.get('Retry-After');
      throw new RateLimitError(
        errorMessage,
        retryAfter ? parseInt(retryAfter, 10) : undefined
      );

    case 500:
    case 502:
    case 503:
    case 504:
      throw new ServiceUnavailableError(errorMessage);

    default:
      throw new NetworkError(errorMessage);
  }
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

/**
 * Build URL with query parameters
 */
export function buildUrl(
  baseUrl: string,
  path: string,
  params?: Record<string, any>
): string {
  const url = new URL(path, baseUrl);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  return url.toString();
}
