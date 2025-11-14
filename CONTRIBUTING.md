# Contributing to Light Show Manager

Thanks for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/light-show-manager.git
   cd light-show-manager
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the code style guidelines below

3. Add or update tests as needed

4. Run the test suite:
   ```bash
   pytest
   ```

5. Check code formatting and linting:
   ```bash
   black lightshow/ tests/
   ruff check lightshow/
   mypy lightshow/
   ```

### Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 100)
- Use type hints where appropriate
- Write docstrings for public APIs (Google style)
- Keep functions focused and modular

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Test on multiple Python versions if possible (3.8, 3.9, 3.10, 3.11, 3.12)
- Use `pytest.mark.asyncio` for async tests

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add feature", "Fix bug")
- Reference issues when applicable (e.g., "Fix #123")

### Pull Requests

1. Push your branch to your fork on GitHub
2. Create a pull request against the `main` branch
3. Describe your changes in detail
4. Link any related issues
5. Wait for CI tests to pass
6. Address any review feedback

## Project Structure

```
light-show-manager/
├── lightshow/          # Main package code
│   ├── __init__.py
│   ├── manager.py      # LightShowManager class
│   ├── show.py         # Show class
│   ├── timeline.py     # Timeline & TimelineEvent
│   ├── executor.py     # Command executor
│   └── exceptions.py   # Custom exceptions
├── tests/              # Test suite
├── examples/           # Example scripts
└── docs/              # Documentation
```

## Design Principles

1. **Explicit over Implicit**: Separate methods for sync vs async (no auto-detection)
2. **Pure Python**: No dependencies beyond stdlib
3. **Hardware Agnostic**: No knowledge of specific devices
4. **Async-First**: Built on asyncio with thread pool fallback for sync
5. **Reliability**: Always run cleanup hooks, even on errors

## Questions or Issues?

- Open an issue on GitHub for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
