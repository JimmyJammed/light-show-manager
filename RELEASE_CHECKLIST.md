# Release Checklist for light-show-manager

## Pre-Release (You are here! ✓)

- [x] Package structure verified
- [x] All tests passing (55 tests, 81% coverage)
- [x] Examples tested and working
- [x] Author information updated
- [x] GitHub repository URLs updated
- [x] README.md updated with badges
- [x] CHANGELOG.md created
- [x] CONTRIBUTING.md added
- [x] CI/CD workflows configured (.github/workflows/)
- [x] Package builds successfully
- [x] Distribution files pass twine check

## Publishing to PyPI

### 1. Create GitHub Repository (If not done)
```bash
# Initialize git (if needed)
git init
git add .
git commit -m "Initial release v0.1.0"

# Create repo on GitHub and push
git remote add origin https://github.com/JimmyJammed/light-show-manager.git
git branch -M main
git push -u origin main
```

### 2. Create PyPI Account
1. Go to https://pypi.org/account/register/
2. Verify your email
3. Enable 2FA (recommended)

### 3. Create API Token for PyPI
1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: "light-show-manager-github-actions"
5. Scope: "Entire account" (or specific project after first upload)
6. Copy the token (starts with `pypi-`)

### 4. Add PyPI Token to GitHub Secrets
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Paste your PyPI API token
5. Click "Add secret"

### 5. Create First Release

#### Option A: Manual Upload (First time)
```bash
# Build the package
python3 -m build

# Upload to PyPI
twine upload dist/*
# Enter your PyPI credentials when prompted
```

#### Option B: GitHub Release (Recommended)
```bash
# Create and push a git tag
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# Create release on GitHub:
# 1. Go to https://github.com/JimmyJammed/light-show-manager/releases
# 2. Click "Create a new release"
# 3. Choose tag: v0.1.0
# 4. Release title: "v0.1.0 - Initial Release"
# 5. Description: Copy from CHANGELOG.md
# 6. Click "Publish release"
# → GitHub Actions will automatically publish to PyPI!
```

## Post-Release

### 1. Verify Publication
- [ ] Check package on PyPI: https://pypi.org/project/light-show-manager/
- [ ] Test installation: `pip install light-show-manager`
- [ ] Verify examples work with installed package

### 2. Update README badges (if needed)
- [ ] PyPI version badge should show v0.1.0
- [ ] Tests badge should be passing
- [ ] All workflow badges green

### 3. Announce Release
- [ ] Post on GitHub Discussions
- [ ] Share on relevant forums/communities (if applicable)
- [ ] Update any related projects (e.g., govee-python)

## Future Releases

For subsequent releases:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Update `__version__` in `lightshow/__init__.py`
4. Commit changes: `git commit -am "Bump version to X.Y.Z"`
5. Create git tag: `git tag -a vX.Y.Z -m "Release version X.Y.Z"`
6. Push changes and tag: `git push && git push --tags`
7. Create GitHub release → Auto-publishes to PyPI

## Semantic Versioning Guide

- **MAJOR** (1.0.0): Breaking API changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

## Testing PyPI (Optional)

To test the release process first:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ light-show-manager
```

## Package Statistics

- **Version**: 0.1.0
- **Size**: ~15 KB (wheel and source)
- **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Dependencies**: None (pure Python)
- **Test Coverage**: 81%
- **Tests**: 55 passing
- **Lines of Code**: ~1,500

## Support

For issues during release:
- GitHub Issues: https://github.com/JimmyJammed/light-show-manager/issues
- PyPI Help: https://pypi.org/help/
