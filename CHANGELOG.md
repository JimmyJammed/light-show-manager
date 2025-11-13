# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-11-13

### Added
- Initial release of Light Show Manager
- Timeline-based event scheduling system
- Separate sync/async event methods for clarity (`add_sync_event()` vs `add_async_event()`)
- Batch event support for simultaneous execution
- Lifecycle hooks: `pre_show`, `post_show`, `on_event`, `on_error`
- Graceful shutdown with signal handling (always runs post_show cleanup)
- Thread pool executor for sync commands
- Direct await for async commands
- Pure Python implementation with zero dependencies
- Support for Python 3.8+
- Comprehensive test suite (81% coverage)
- Full documentation and examples
- GitHub Actions CI/CD workflows

### Features
- `Show` class for defining light shows
- `LightShowManager` for orchestrating shows
- `Timeline` and `TimelineEvent` for event management
- `Executor` for sync/async command execution
- Hardware-agnostic design
- Context manager support
- Error handling with custom exceptions

[unreleased]: https://github.com/JimmyJammed/light-show-manager/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JimmyJammed/light-show-manager/releases/tag/v0.1.0
