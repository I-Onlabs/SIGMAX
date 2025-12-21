# Changelog

All notable changes to the SIGMAX TypeScript SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-21

### Added

- Initial release of SIGMAX TypeScript SDK
- Full TypeScript support with complete type definitions
- Dual package support (ESM and CommonJS)
- Browser and Node.js compatibility
- Zero runtime dependencies
- Comprehensive API coverage:
  - Analysis methods (`analyze`, `analyzeStream`, `getAgentDebate`)
  - Trade proposal methods (`proposeTradeProposal`, `listProposals`, `approveProposal`, `executeProposal`)
  - Portfolio methods (`getPortfolio`, `getTradeHistory`)
  - System control methods (`startTrading`, `pauseTrading`, `stopTrading`, `emergencyStop`)
  - Health check methods (`healthCheck`, `readinessCheck`, `livenessCheck`)
  - Monitoring methods (`getStatus`, `getMetrics`)
  - Quantum methods (`getQuantumCircuit`)
- Server-Sent Events (SSE) streaming support
- Comprehensive error handling with custom error types:
  - `AuthenticationError`
  - `RateLimitError`
  - `ValidationError`
  - `NotFoundError`
  - `PermissionError`
  - `ServiceUnavailableError`
  - `TimeoutError`
  - `NetworkError`
- Complete examples:
  - Basic usage (TypeScript)
  - Streaming analysis (TypeScript)
  - Node.js CommonJS example
  - Browser HTML example
- Full documentation in README.md
- Build scripts for dual package output
- MIT License

### Features

- **Type Safety**: Full TypeScript definitions for all API methods and responses
- **Streaming**: Real-time analysis updates via SSE with async iterator pattern
- **Error Handling**: Proper HTTP status code to error type mapping
- **Rate Limiting**: Automatic detection and reporting of rate limit errors
- **Timeouts**: Configurable request timeouts with proper abort handling
- **Browser Support**: Works in modern browsers with native fetch API
- **Tree Shaking**: ESM exports allow for optimal bundle sizes
- **Zero Config**: Works out of the box with sensible defaults

### Documentation

- Comprehensive README with full API reference
- TypeScript usage examples
- Error handling examples
- Streaming examples
- Installation instructions for npm, yarn, and pnpm

[1.0.0]: https://github.com/yourusername/sigmax/releases/tag/v1.0.0
