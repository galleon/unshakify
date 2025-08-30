# UV Guide - Fast Python Package Management for Unshakify

This guide covers everything you need to know about using [uv](https://github.com/astral-sh/uv) with the Unshakify video stabilization project.

## Why UV?

uv is a blazing fast Python package manager written in Rust that provides:

- ⚡ **10-100x faster** installation than pip
- 🔒 **Deterministic builds** with automatic lockfile management
- 🚀 **Built-in virtual environment management**
- 📦 **Better dependency caching** and parallel downloads
- 🛡️ **More reliable** dependency resolution

## Quick Start

### 1. Install UV

```bash
# On macOS and Linux (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip (if you must)
pip install uv

# Verify installation
uv --version
```

**Important**: Restart your terminal after installation to ensure PATH is updated.

### 2. Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd unshakify

# Automatic setup (Mac M3 users)
uv run python setup_mac_m3.py

# Or manual setup
uv sync                           # Creates venv and installs dependencies
uv pip install -e .[mac-m3]      # Add Mac M3 optimizations
```

### 3. Run the Application

```bash
# Main comparison demo
uv run python main.py

# Simple runner with options
uv run python run.py --test      # Run tests
uv run python run.py --demo      # Advanced demo
uv run python run.py --status    # Check status
```

## Core UV Commands for Unshakify

### Environment Management

```bash
# Create virtual environment and install dependencies
uv sync

# Install project in editable mode with optional dependencies
uv pip install -e .[mac-m3]      # Mac M3 optimizations
uv pip install -e .[dev]         # Development tools
uv pip install -e .[all]         # Everything

# Check environment status
uv pip list                       # List installed packages
uv pip freeze                     # Export requirements
```

### Running Scripts

```bash
# Always use 'uv run' to execute Python scripts
uv run python main.py            # Main demo
uv run python tests/test_fast_stab.py  # Tests
uv run pytest tests/             # Full test suite

# Run with specific Python version
uv run --python 3.11 python main.py
```

### Dependency Management

```bash
# Add new dependencies
uv add opencv-python              # Add to main dependencies
uv add --dev pytest-benchmark    # Add to dev dependencies

# Remove dependencies
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Lock dependencies for reproducible installs
uv lock
```

## Installation Profiles

Unshakify offers several installation profiles optimized for different use cases:

### Basic Installation
```bash
uv pip install -e .
```
**Includes**: OpenCV, NumPy (minimum for basic functionality)

### Mac M3 Optimized
```bash
uv pip install -e .[mac-m3]
```
**Includes**: Basic + opencv-contrib-python-headless (ARM64 optimized)

### Development Environment
```bash
uv pip install -e .[dev]
```
**Includes**: Basic + pytest, ruff, mypy (testing and code quality tools)

### Full Development
```bash
uv pip install -e .[dev,full]
```
**Includes**: Dev + pre-commit, black, isort (complete development setup)

### Everything
```bash
uv pip install -e .[all]
```
**Includes**: All optional dependencies for maximum functionality

### Performance Testing
```bash
uv pip install -e .[benchmark]
```
**Includes**: Basic + pytest-benchmark, memory-profiler, psutil

## Daily Workflow with UV

### Development Workflow

```bash
# Start working on the project
cd unshakify
uv sync                           # Ensure environment is up to date

# Run the application
uv run python main.py

# Run tests while developing
uv run python run.py --test      # Quick compatibility test
uv run pytest tests/             # Full test suite

# Code quality checks
uv run ruff check .               # Lint code
uv run ruff format .              # Format code
uv run mypy src/                  # Type checking

# Install new dependencies
uv add new-package                # Add runtime dependency
uv add --dev pytest-plugin       # Add development dependency
```

### Testing Workflow

```bash
# Quick tests
uv run python run.py --test      # Compatibility tests
uv run python run.py --status    # Check project status

# Comprehensive testing
uv run pytest tests/             # Full test suite
uv run pytest --cov=src/         # With coverage

# Performance testing
uv run python -m cProfile main.py  # Profile performance
```

### Demo and Comparison Workflow

```bash
# Main comparison (runs all stabilizers)
uv run python main.py

# Advanced demos
uv run python run.py --demo      # Detailed comparison
uv run python tests/demo_fast_stab.py  # Direct advanced demo

# Check if sample video is available
uv run python run.py --check
```

## Troubleshooting UV Issues

### Common Problems and Solutions

#### Problem: "uv: command not found"
```bash
# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal after installation
```

#### Problem: Dependencies not found
```bash
# Solution: Sync environment
uv sync

# Or reinstall with specific profile
uv pip install -e .[mac-m3]
```

#### Problem: Virtual environment issues
```bash
# Solution: Clean and recreate environment
rm -rf .venv
uv sync
```

#### Problem: Lock file conflicts
```bash
# Solution: Update lock file
uv lock --upgrade
uv sync
```

### Performance Issues

#### Slow installation
```bash
# Check if you're using the latest uv
uv self update

# Use parallel downloads (default in uv)
uv sync --no-cache  # Force fresh download
```

#### Import errors
```bash
# Ensure you're using uv run
uv run python your_script.py

# Check if packages are installed
uv pip list | grep opencv
```

### Mac M3 Specific Issues

#### Problem: Architecture mismatch
```bash
# Verify you're on ARM64
uv run python -c "import platform; print(platform.machine())"
# Should output: arm64

# Install Mac M3 optimized packages
uv pip install -e .[mac-m3]
```

#### Problem: OpenCV not optimized for Apple Silicon
```bash
# Ensure opencv-contrib-python-headless is installed
uv pip install opencv-contrib-python-headless

# Check OpenCV build info
uv run python -c "import cv2; print(cv2.getBuildInformation())"
```

## Advanced UV Features

### Environment Isolation

```bash
# Create isolated environment for testing
uv venv test-env
source test-env/bin/activate  # or test-env\Scripts\activate on Windows

# Install in isolated environment
uv pip install -e .

# Deactivate and remove
deactivate
rm -rf test-env
```

### Multiple Python Versions

```bash
# Use specific Python version
uv run --python 3.11 python main.py
uv run --python 3.12 python main.py

# Install with specific Python version
uv pip install --python 3.11 -e .
```

### Lock File Management

```bash
# Generate lock file (automatic with uv sync)
uv lock

# Update lock file with new versions
uv lock --upgrade

# Install from lock file on different machine
uv sync  # Installs exact versions from uv.lock
```

## Migrating from pip to UV

If you were previously using pip, here's how to migrate:

### Old pip workflow:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py
```

### New uv workflow:
```bash
uv sync                    # Creates venv and installs dependencies
uv run python main.py     # Runs in managed environment
```

### Converting pip requirements:
```bash
# If you have a requirements.txt
uv pip install -r requirements.txt

# Better: use pyproject.toml dependencies (already configured)
uv sync
```

## Best Practices

### Do's ✅

- **Always use `uv run`** for executing Python scripts
- **Commit `uv.lock`** to version control for reproducible installs
- **Use `uv sync`** to keep environment up to date
- **Use installation profiles** (`[mac-m3]`, `[dev]`, etc.) for different needs
- **Update uv regularly** with `uv self update`

### Don'ts ❌

- **Don't mix pip and uv** in the same environment
- **Don't manually activate virtual environments** (uv manages this)
- **Don't ignore `uv.lock` conflicts** - resolve them with `uv lock --upgrade`
- **Don't use `python` directly** - always use `uv run python`

## Integration with IDEs

### VS Code

Add to your VS Code settings:

```json
{
    "python.terminal.activateEnvironment": false,
    "python.defaultInterpreterPath": "./.venv/bin/python"
}
```

### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Add New Interpreter → Existing Environment
3. Point to `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

## Performance Comparison

| Operation | pip | uv | Improvement |
|-----------|-----|----|-----------| 
| Install project | ~30s | ~3s | **10x faster** |
| Install dependencies | ~45s | ~5s | **9x faster** |
| Environment creation | ~10s | ~2s | **5x faster** |
| Dependency resolution | ~20s | ~1s | **20x faster** |

## Getting Help

### UV Resources
- 📖 [Official UV Documentation](https://github.com/astral-sh/uv)
- 🐛 [UV Issue Tracker](https://github.com/astral-sh/uv/issues)
- 💬 [UV Discussions](https://github.com/astral-sh/uv/discussions)

### Unshakify-Specific Help
```bash
# Check project status
uv run python run.py --status

# Run compatibility tests
uv run python run.py --test

# Get help with runner
uv run python run.py --help
```

### Quick Diagnostics
```bash
# Check uv version
uv --version

# Check Python in managed environment
uv run python --version

# List installed packages
uv pip list

# Check if unshakify is properly installed
uv run python -c "import unshakify; print('✅ Unshakify imported successfully')"
```

---

**Remember**: uv is not just a faster pip - it's a complete Python project management solution. Embrace its workflow for the best experience with Unshakify! 🚀