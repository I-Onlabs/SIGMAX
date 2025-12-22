/**
 * SIGMAX Error Classes Tests
 */

import { describe, it, expect } from 'vitest';
import {
  SigmaxError,
  AuthenticationError,
  NetworkError,
  ValidationError,
  RateLimitError,
  TimeoutError,
} from './errors';

describe('Error Classes', () => {
  describe('SigmaxError', () => {
    it('should create base error with message', () => {
      const error = new SigmaxError('Test error');
      expect(error).toBeInstanceOf(Error);
      expect(error.message).toBe('Test error');
      expect(error.name).toBe('SigmaxError');
    });

    it('should be catchable as Error', () => {
      try {
        throw new SigmaxError('Test');
      } catch (err) {
        expect(err).toBeInstanceOf(Error);
        expect(err).toBeInstanceOf(SigmaxError);
      }
    });
  });

  describe('AuthenticationError', () => {
    it('should create authentication error', () => {
      const error = new AuthenticationError('Invalid API key');
      expect(error).toBeInstanceOf(SigmaxError);
      expect(error.message).toBe('Invalid API key');
      expect(error.name).toBe('AuthenticationError');
    });

    it('should use default message when none provided', () => {
      const error = new AuthenticationError();
      expect(error.message).toBe('Invalid or missing API key');
    });
  });

  describe('NetworkError', () => {
    it('should create network error', () => {
      const error = new NetworkError('Connection failed');
      expect(error).toBeInstanceOf(SigmaxError);
      expect(error.message).toBe('Connection failed');
      expect(error.name).toBe('NetworkError');
    });
  });

  describe('ValidationError', () => {
    it('should create validation error', () => {
      const error = new ValidationError('Validation failed');
      expect(error).toBeInstanceOf(SigmaxError);
      expect(error.message).toBe('Validation failed');
      expect(error.name).toBe('ValidationError');
    });
  });

  describe('RateLimitError', () => {
    it('should create rate limit error with retry after', () => {
      const error = new RateLimitError('Rate limit exceeded. Retry after 60 seconds', 60);
      expect(error).toBeInstanceOf(SigmaxError);
      expect(error.message).toBe('Rate limit exceeded. Retry after 60 seconds');
      expect(error.retryAfter).toBe(60);
      expect(error.name).toBe('RateLimitError');
    });

    it('should handle missing retry after', () => {
      const error = new RateLimitError('Rate limit exceeded');
      expect(error.retryAfter).toBeUndefined();
    });
  });

  describe('TimeoutError', () => {
    it('should create timeout error with timeout value', () => {
      const error = new TimeoutError(30000);
      expect(error).toBeInstanceOf(SigmaxError);
      expect(error.message).toBe('Request timed out after 30000ms');
      expect(error.name).toBe('TimeoutError');
    });
  });

  // Error inheritance chain tests
  describe('inheritance chain', () => {
    it('all custom errors should inherit from SigmaxError', () => {
      expect(new AuthenticationError('test')).toBeInstanceOf(SigmaxError);
      expect(new NetworkError('test')).toBeInstanceOf(SigmaxError);
      expect(new ValidationError('test')).toBeInstanceOf(SigmaxError);
      expect(new RateLimitError('test')).toBeInstanceOf(SigmaxError);
      expect(new TimeoutError(5000)).toBeInstanceOf(SigmaxError);
    });

    it('all custom errors should inherit from Error', () => {
      expect(new SigmaxError('test')).toBeInstanceOf(Error);
      expect(new AuthenticationError('test')).toBeInstanceOf(Error);
      expect(new NetworkError('test')).toBeInstanceOf(Error);
      expect(new ValidationError('test')).toBeInstanceOf(Error);
      expect(new RateLimitError('test')).toBeInstanceOf(Error);
      expect(new TimeoutError(5000)).toBeInstanceOf(Error);
    });
  });

  // Error catching and handling tests
  describe('error catching', () => {
    it('should catch specific error types', () => {
      try {
        throw new AuthenticationError('Invalid credentials');
      } catch (err) {
        if (err instanceof AuthenticationError) {
          expect(err.message).toBe('Invalid credentials');
        } else {
          throw new Error('Wrong error type caught');
        }
      }
    });

    it('should distinguish between error types', () => {
      const authError = new AuthenticationError('auth');
      const networkError = new NetworkError('network');

      expect(authError).toBeInstanceOf(AuthenticationError);
      expect(authError).not.toBeInstanceOf(NetworkError);

      expect(networkError).toBeInstanceOf(NetworkError);
      expect(networkError).not.toBeInstanceOf(AuthenticationError);
    });
  });
});
