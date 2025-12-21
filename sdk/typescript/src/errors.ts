/**
 * SIGMAX TypeScript SDK - Error Classes
 */

/**
 * Base error class for SIGMAX SDK errors
 */
export class SigmaxError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SigmaxError';
    Object.setPrototypeOf(this, SigmaxError.prototype);
  }
}

/**
 * Error thrown when API key is missing or invalid
 */
export class AuthenticationError extends SigmaxError {
  constructor(message = 'Invalid or missing API key') {
    super(message);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

/**
 * Error thrown when rate limit is exceeded
 */
export class RateLimitError extends SigmaxError {
  public retryAfter?: number;

  constructor(message: string, retryAfter?: number) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
    Object.setPrototypeOf(this, RateLimitError.prototype);
  }
}

/**
 * Error thrown for invalid request parameters
 */
export class ValidationError extends SigmaxError {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Error thrown when a resource is not found
 */
export class NotFoundError extends SigmaxError {
  constructor(resource: string, id?: string) {
    const message = id
      ? `${resource} with ID '${id}' not found`
      : `${resource} not found`;
    super(message);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

/**
 * Error thrown when permission is denied
 */
export class PermissionError extends SigmaxError {
  constructor(message: string) {
    super(message);
    this.name = 'PermissionError';
    Object.setPrototypeOf(this, PermissionError.prototype);
  }
}

/**
 * Error thrown when the service is unavailable
 */
export class ServiceUnavailableError extends SigmaxError {
  constructor(message = 'Service temporarily unavailable') {
    super(message);
    this.name = 'ServiceUnavailableError';
    Object.setPrototypeOf(this, ServiceUnavailableError.prototype);
  }
}

/**
 * Error thrown when request times out
 */
export class TimeoutError extends SigmaxError {
  constructor(timeout: number) {
    super(`Request timed out after ${timeout}ms`);
    this.name = 'TimeoutError';
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

/**
 * Error thrown for network-related issues
 */
export class NetworkError extends SigmaxError {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}
