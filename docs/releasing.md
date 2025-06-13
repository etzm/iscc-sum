# Release Process for iscc-sum

This document describes the release process for the iscc-sum project, which includes both a Rust CLI tool and a
Python library with Rust extensions.

## Prerequisites

### Required Accounts

1. **crates.io account** - For publishing the Rust crate

   - Create an account at https://crates.io
   - Generate an API token from your account settings

2. **PyPI account** - For publishing the Python package

   - The project uses PyPI trusted publishing (OIDC)
   - No API token needed - authentication happens through GitHub Actions

### GitHub Repository Secrets

Configure the following secret in your GitHub repository settings:

- `CRATES_IO_TOKEN` - Your crates.io API token

To add the secret:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CRATES_IO_TOKEN`
4. Value: Your crates.io API token

## Version Management

The project uses semantic versioning (SemVer) with the format `MAJOR.MINOR.PATCH[-PRERELEASE]`.

Current version locations:

- `Cargo.toml` - Rust crate version
- `pyproject.toml` - Python package version

Both versions must be kept in sync.

### Pre-release Identifiers

- `alpha` - Early development releases (e.g., `0.1.0-alpha.1`)
- `beta` - Feature-complete but still testing (e.g., `0.1.0-beta.1`)
- `rc` - Release candidate (e.g., `0.1.0-rc.1`)

## Automated Release Process

The project uses [Release Please](https://github.com/googleapis/release-please) for automated release
management.

### How It Works

1. **Commit to main branch** - Use conventional commit messages:

   - `feat:` - New features (bumps MINOR version)
   - `fix:` - Bug fixes (bumps PATCH version)
   - `feat!:` or `BREAKING CHANGE:` - Breaking changes (bumps MAJOR version)

2. **Release Please creates PR** - Automatically generated when commits are pushed to main

   - Updates version numbers in `Cargo.toml`
   - Generates/updates CHANGELOG.md
   - Creates release notes

3. **Merge the Release PR** - This triggers:

   - Version sync to `pyproject.toml`
   - Git tag creation (e.g., `v0.1.0`)
   - GitHub release creation

4. **Release workflow runs** - Triggered by the version tag:

   - Builds binaries for multiple platforms
   - Builds Python wheels for multiple Python versions
   - Publishes to crates.io
   - Publishes to PyPI
   - Uploads artifacts to GitHub release

### Release Workflow Details

The release workflow (`release.yml`) performs:

1. **Rust Binary Builds**

   - Linux (x86_64)
   - Windows (x86_64)
   - macOS (x86_64, ARM64)

2. **Python Wheel Builds**

   - Python 3.10-3.13
   - Linux, Windows, macOS
   - Both x86_64 and ARM64 architectures where applicable

3. **Publishing**

   - Publishes Rust crate to crates.io
   - Publishes Python package to PyPI
   - Creates GitHub release with all artifacts

## Manual Release Process

If you need to create a release manually:

### 1. Update Versions

Update version in both files:

```bash
# Edit Cargo.toml
version = "0.1.0"

# Edit pyproject.toml
version = "0.1.0"
```

### 2. Create Release Commit

```bash
git add Cargo.toml pyproject.toml
git commit -m "chore: release 0.1.0"
git push origin main
```

### 3. Create and Push Tag

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

This will trigger the release workflow automatically.

### 4. Manual Publishing (if automated publishing fails)

#### Publish to crates.io:

```bash
cargo publish
```

#### Publish to PyPI:

```bash
# Build distributions
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Pre-release Testing

Before creating a release:

1. **Run all checks locally**:

   ```bash
   uv run poe all
   ```

2. **Verify CI passes** - Check that all GitHub Actions workflows are green

3. **Test installations**:

   ```bash
   # Test Rust installation
   cargo install --path .

   # Test Python installation
   pip install -e .
   ```

## Troubleshooting

### Common Issues

1. **Version mismatch** - Ensure Cargo.toml and pyproject.toml versions match
2. **CI failures** - Run `uv run poe all` locally to catch issues early
3. **Publishing failures** - Check that secrets are correctly configured

### Release Workflow Failures

If the release workflow fails:

1. Check the GitHub Actions logs for specific errors
2. Verify all secrets are configured correctly
3. Ensure you have the necessary permissions on crates.io and PyPI

## Version Bumping Guidelines

- **PATCH** (0.0.X) - Bug fixes, documentation updates
- **MINOR** (0.X.0) - New features, backwards-compatible changes
- **MAJOR** (X.0.0) - Breaking changes (after 1.0.0)

While in 0.x.x versions:

- Breaking changes can happen in MINOR versions
- The project is considered unstable

## Post-Release Checklist

After a successful release:

1. Verify the release appears on:
   - GitHub releases page
   - crates.io
   - PyPI
2. Test installation from the published packages
3. Update any documentation that references the version
4. Announce the release if appropriate
