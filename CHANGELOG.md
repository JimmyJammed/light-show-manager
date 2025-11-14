# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Logger Module** - Color-coded console and file logging system
  - `Logger` class with color-coded output (INFO=white, WARN=yellow, ERROR=red, DEBUG=cyan)
  - File logging to timestamped log files (`log_YYYY_MM_DD_HH_MM_SS.log`)
  - Automatic TTY detection for color support
  - Respects `NO_COLOR` environment variable
  - Optional timestamps (enabled by default)
  - Context manager support for automatic cleanup
  - Caller information in file logs (filename, line number, function)
  - Convenience methods: `info()`, `warn()`, `error()`, `debug()`
  - Default logger instance for quick usage
- **Logging Bridge** - Integrate Python's standard logging with lightshow Logger
  - `configure_stdlib_logging()` to route stdlib logs through lightshow Logger
  - Unified logging for third-party libraries (e.g., govee-python)
  - Automatic level mapping (DEBUG→debug, INFO→info, WARNING→warn, ERROR→error)
  - Supports specific logger names or root logger configuration
  - `reset_stdlib_logging()` to revert to default behavior
- Added `logs/` to `.gitignore`

## [0.2.0] - 2024-11-13

### Added
- **Device State Management** - Automatic tracking and restoration of device states
  - `with_device_state_management()` decorator for show builders
  - Tracks device usage automatically during show construction
  - Integrates with user-defined save/restore hooks
  - Supports spotlight devices (turned off before show)
  - Generic implementation - works with any device library
  - Example usage in README with Govee integration

### Changed
- Version bumped to 0.2.0
- Updated README with device state management examples
- Enhanced feature documentation

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
