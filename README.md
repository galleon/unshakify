# Unshakify - AI-Based Video Stabilization

Unshakify is a lightweight, real-time video stabilization system that computes key performance indicators for AI-based image stabilizers. It includes both a basic stabilizer and an advanced Fast-Stab inspired stabilizer optimized for Mac M3 (Apple Silicon). The system uses computer vision techniques to analyze camera motion, apply smoothing transformations, and measure the quality of stabilization results.

## Features

### Core Stabilization
- **Real-time Processing**: Online stabilizers that process frames sequentially with minimal latency
- **Multiple Algorithms**: Choose between basic KLT tracking or advanced Fast-Stab inspired methods
- **Smooth Stabilization**: Applies exponential moving average (EMA) smoothing to camera motion paths
- **Comprehensive Metrics**: Computes multiple indicators to evaluate stabilization quality
- **Mac M3 Optimized**: Fast-Stab stabilizer optimized for Apple Silicon performance

### Stabilization Methods
1. **OnlineStabilizer** (Basic):
   - KLT (Kanade-Lucas-Tomasi) feature tracking
   - Robust affine transformation estimation
   - Lightweight and fast processing

2. **FastStabilizer** (Advanced - Fast-Stab Inspired):
   - Dense or sparse optical flow estimation
   - Confidence map generation for better feature filtering
   - Homography-based transformations for perspective handling
   - Adaptive temporal smoothing based on motion confidence
   - Compatible with Mac M3 Apple Silicon

### Dependencies
- **Minimal Core**: Only requires OpenCV and NumPy
- **Mac M3 Support**: Optimized builds for Apple Silicon architecture

## Performance Indicators

The system computes four key indicators to evaluate stabilization performance:

### 1. Processing Latency
- **Metric**: Milliseconds per frame (ms/frame)
- **Description**: Average processing time required to stabilize each frame
- **Lower is better**: Indicates faster processing capability

### 2. Stability Score
- **Metric**: RMS of per-frame translation magnitudes
- **Description**: Measures camera shake reduction effectiveness
- **Improvement calculation**: `1 - (S_after / S_before)` where higher values indicate better stabilization

### 3. Cropping Ratio
- **Metric**: Fraction of valid (non-black) pixels retained (0-1)
- **Description**: Measures how much of the original frame content is preserved
- **1.0 = no cropping**: Higher values preserve more of the original field of view

### 4. Distortion Value
- **Metric**: `1 - SSIM` between original and stabilized frames
- **Description**: Measures fidelity to the original video content
- **Lower is better**: Indicates less distortion introduced by stabilization

## Installation

**Using uv (Required - 10-100x Faster!)**

This project is optimized for [uv](https://github.com/astral-sh/uv), a blazing fast Python package manager written in Rust. uv is **required** for the best experience and performance.

**Why uv is essential:**
- ⚡ **10-100x faster** than pip for installation and dependency resolution
- 🔒 **Deterministic builds** with automatic lockfile management
- 🚀 **Built-in virtual environment management** (no need for separate venv)
- 📦 **Better dependency caching** and parallel downloads
- 🛡️ **More reliable** dependency resolution with conflict detection

### Quick Setup (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and setup the project
git clone <repository-url>
cd unshakify

# For Mac M3 users - automated setup
uv run python setup_mac_m3.py

# Or manual installation
uv sync                          # Creates venv and installs dependencies
uv pip install -e .[mac-m3]     # Adds Mac M3 optimizations
```

### Installation Options with uv

```bash
# Basic installation
uv pip install -e .

# Mac M3 optimized (recommended for Apple Silicon)
uv pip install -e .[mac-m3]

# Development environment
uv pip install -e .[dev]

# Full development with all tools
uv pip install -e .[dev,full]

# Everything (all optional dependencies)
uv pip install -e .[all]
```

### Fallback: Using pip (Not Recommended)

If you absolutely cannot use uv, you can fall back to pip, but expect slower performance:

```bash
# Create virtual environment manually
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with pip (slower)
pip install -e .[mac-m3]
```

**Note**: The setup scripts and documentation assume uv usage. Some features may not work optimally with pip.

## Usage

### Basic Example

```python
from unshakify.stabilizer import OnlineStabilizer, write_stabilized_video
from unshakify.fast_stabilizer import FastStabilizer, write_fast_stabilized_video
from unshakify.indicators import (
    measure_latency,
    stability_score_from_video,
    stability_improvement,
    cropping_ratio_from_video,
    distortion_value_from_videos,
)

# Input and output video paths
raw_video = "raw.mp4"
stabilized_video = "stab.mp4"

# Initialize stabilizer
stabilizer = OnlineStabilizer(alpha=0.90)

# 1. Measure processing latency
latency_ms = measure_latency(raw_video, stabilizer, warmup_frames=5, max_frames=300)
print(f"Latency: {latency_ms:.2f} ms/frame")

# 2. Generate stabilized video
write_stabilized_video(raw_video, stabilized_video, stabilizer, fourcc="mp4v")

# 3. Compute quality indicators
S_before = stability_score_from_video(raw_video)
S_after = stability_score_from_video(stabilized_video)
S_improvement = stability_improvement(raw_video, stabilized_video)
cropping_ratio = cropping_ratio_from_video(stabilized_video)
distortion_value = distortion_value_from_videos(raw_video, stabilized_video)

# 4. Display results
print(f"Stability before: {S_before:.3f}")
print(f"Stability after : {S_after:.3f}")
print(f"Stability improvement: {S_improvement:.3f}  (0–1, higher is better)")
print(f"Cropping ratio: {cropping_ratio:.3f}       (1.0 = no crop)")
print(f"Distortion value: {distortion_value:.3f}       (lower is better)")
```

### Fast-Stab Inspired Stabilizer (Advanced)

For more advanced stabilization with better motion handling:

```python
from unshakify.fast_stabilizer import FastStabilizer, write_fast_stabilized_video

# Input and output video paths
raw_video = "raw.mp4"
stabilized_video = "stab_fast.mp4"

# Initialize FastStabilizer with different flow methods
stabilizer_lk = FastStabilizer(
    alpha=0.85,                    # Temporal smoothing factor
    flow_method="lucas_kanade",    # or "farneback" for dense flow
    confidence_threshold=0.6,      # Minimum confidence for flow points
    min_flow_points=500,           # Minimum points needed for stabilization
    max_corners=1000               # Maximum corners for LK method
)

# Alternative: Dense optical flow method
stabilizer_dense = FastStabilizer(
    alpha=0.9,
    flow_method="farneback",       # Dense optical flow
    confidence_threshold=0.5
)

# Process video
write_fast_stabilized_video(raw_video, stabilized_video, stabilizer_lk, fourcc="mp4v")

# Get stabilization information
info = stabilizer_lk.get_stabilization_info()
print(f"Average confidence: {info['avg_confidence']:.3f}")
print(f"Transform complexity: {info['transform_norm']:.3f}")
```

### Running the Main Demo

The main script compares both stabilizers and provides comprehensive performance analysis:

**Using uv (standard approach):**
```bash
uv run python main.py
```

**Or use the simple runner:**
```bash
uv run python run.py              # Same as main.py
uv run python run.py --test       # Run tests
uv run python run.py --demo       # Advanced demo
```

Expected output:
```
🎬 UNSHAKIFY - AI-BASED VIDEO STABILIZATION COMPARISON
======================================================================
Comparing OnlineStabilizer vs FastStabilizer performance

1️⃣  RUNNING BASIC ONLINE STABILIZER
--------------------------------------------------
📊 Measuring processing latency...
   ⏱️  Latency measurement: 20.15 ms/frame (took 2.1s)
🎥 Processing full video...
   ✅ Video processing completed in 15.3s

2️⃣  RUNNING FAST STABILIZER (Lucas-Kanade)
--------------------------------------------------
📊 Measuring processing latency...
   ⏱️  Latency measurement: 18.42 ms/frame (took 2.3s)

📊 PERFORMANCE COMPARISON RESULTS
======================================================================
🚀 Fastest processing: FastStabilizer (Farneback) (18.4 ms/frame)
⭐ Best stabilization: FastStabilizer (Lucas-Kanade) (0.045 improvement)
```

### Additional Tests and Demos

**Compatibility testing:**
```bash
uv run python tests/test_fast_stab.py
```

**Advanced comparison demo:**
```bash
uv run python tests/demo_fast_stab.py
```

**Using the runner shortcuts:**
```bash
uv run python run.py --test       # Compatibility tests
uv run python run.py --demo       # Advanced demo
uv run python run.py --check      # Check if video file exists
```

These additional scripts provide detailed testing and analysis of specific stabilizer features.

## Algorithm Details

### Motion Estimation
- **Feature Detection**: Uses `cv2.goodFeaturesToTrack()` to detect corner features
- **Optical Flow**: Tracks features between consecutive frames using Lucas-Kanade method
- **Robust Estimation**: Uses RANSAC with `cv2.estimateAffinePartial2D()` to estimate rigid motion (translation + rotation, no scaling)

### Stabilization Process
1. **Motion Accumulation**: Tracks cumulative camera motion `[dx, dy, da]` (translation + rotation)
2. **Path Smoothing**: Applies exponential moving average to create smooth camera trajectory
3. **Compensation**: Applies the difference between smoothed and raw motion to stabilize frames
4. **Boundary Handling**: Uses black padding to maintain full field of view

### Configurable Parameters
- `alpha` (0-1): Smoothing factor for EMA - higher values = smoother but more latency
- `ransac_thresh`: RANSAC threshold for robust motion estimation
- `max_frames`: Limit processing to specific number of frames for testing

## Project Structure

```
unshakify/
├── src/
│   └── unshakify/
│       ├── __init__.py
│       ├── stabilizer.py      # Core stabilization algorithm
│       └── indicators.py      # Performance metrics computation
├── main.py                    # Demo script
├── pyproject.toml            # Project configuration
├── raw.mp4                   # Sample input video
└── README.md                 # This file
```

## Requirements

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OpenCV Python (headless) ≥ 4.8.0
- NumPy ≥ 1.24.0

### Mac M3 (Apple Silicon) Users

For optimal performance on Mac M3, use the automated setup script:

```bash
uv run python setup_mac_m3.py
```

This will:
- Check system compatibility and uv installation
- Create optimized virtual environment with uv
- Install Mac M3 specific dependencies (opencv-contrib, ARM64 optimizations)
- Set up FFmpeg for better video codec support
- Run compatibility tests
- Provide performance optimization tips

You can also install dependencies manually:
```bash
uv pip install -e .[mac-m3]
```

**Why Mac M3 optimization matters:**
- Uses ARM64 native OpenCV builds (up to 2x faster)
- Leverages Apple's Accelerate framework through NumPy
- Optimized memory usage for Apple Silicon architecture
- Better GPU utilization where available

### Installing uv (Required)

uv is **required** for optimal performance. Install it before proceeding:

```bash
# On macOS and Linux (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip (if you must, but slower)
pip install uv

# Verify installation
uv --version
```

**After installing uv, restart your terminal** to ensure the PATH is updated.

### Available Installation Options with uv

The project supports several installation configurations, all optimized for uv:

```bash
# Basic installation (minimum dependencies)
uv pip install -e .

# Mac M3 optimized (includes opencv-contrib and ARM64 optimizations)
uv pip install -e .[mac-m3]

# Development environment (includes testing and linting tools)  
uv pip install -e .[dev]

# Full development with all tools
uv pip install -e .[dev,full]

# Multimedia support (includes ffmpeg-python)
uv pip install -e .[multimedia]

# Performance testing tools
uv pip install -e .[benchmark]

# Everything (all optional dependencies)
uv pip install -e .[all]
```

**Pro tip**: Use `uv sync` to automatically create a virtual environment and install all dependencies based on the lock file.

## Code Quality

This project uses `ruff` for fast Python linting and formatting. All configuration is centralized in `pyproject.toml` and optimized for uv:

```bash
# Check code quality (uv manages the environment)
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .
```

### Pre-commit Workflow

Before committing code, run:
```bash
# Format and fix issues
uv run ruff format .
uv run ruff check --fix .

# Test the code still works
uv run python main.py

# Run full test suite
uv run pytest tests/
```

### Development Environment Setup

```bash
# Install development tools
uv pip install -e .[dev,full]

# Run type checking
uv run mypy src/

# Run tests with coverage
uv run pytest tests/ --cov=src/unshakify
```

## Performance Characteristics

The system is designed for:
- **Real-time processing**: Typical latency < 25ms per frame on modern hardware
- **Memory efficiency**: Processes frames sequentially without storing entire videos
- **Robustness**: Handles cases with insufficient features or motion estimation failures
- **Quality preservation**: Maintains high fidelity with minimal distortion

## Applications

This stabilization system and its indicators are particularly useful for:
- **Referee camera stabilization**: Reducing shake in sports video capture
- **Mobile video enhancement**: Improving handheld video quality
- **Drone footage stabilization**: Compensating for flight vibrations
- **Performance benchmarking**: Evaluating different stabilization algorithms
- **Research and development**: Testing new motion estimation techniques

## License

This project is open source. See the license file for details.

## Development

### Setting up for Development

```bash
# Clone the repository
git clone <repository-url>
cd unshakify

# For Mac M3 users (fully automated setup)
uv run python setup_mac_m3.py

# Or manual setup with uv
uv sync                               # Creates venv and installs dependencies
uv pip install -e .[mac-m3,dev]      # Add Mac M3 + development tools

# Verify installation
uv run python tests/test_fast_stab.py  # Compatibility tests
uv run pytest tests/                   # Full test suite

# Run demos
uv run python main.py                  # Main comparison demo
uv run python run.py --demo           # Advanced demo via runner
```

**Development workflow with uv:**
```bash
# Install new dependencies
uv add package-name

# Install development-only dependencies  
uv add --dev pytest-new-plugin

# Update all dependencies
uv sync --upgrade

# Run in managed environment
uv run python your-script.py
```

### Development Commands with uv

```bash
# Dependency management
uv add package-name              # Add new dependency
uv add --dev pytest-plugin       # Add development dependency
uv remove package-name           # Remove dependency
uv sync                         # Sync environment with lock file
uv sync --upgrade               # Update all dependencies

# Project installation variants
uv pip install -e .[mac-m3,dev] # Mac M3 + development tools
uv pip install -e .[dev,full]   # Full development environment
uv pip install -e .[all]        # Everything

# Code quality and testing
uv run ruff check .             # Lint code
uv run ruff format .            # Format code
uv run mypy src/                # Type checking
uv run pytest tests/           # Run all tests
uv run pytest --cov=src/       # Test with coverage

# Run applications
uv run python main.py           # Main demo
uv run python run.py --test     # Quick test runner
uv run --python 3.11 python main.py  # Specific Python version

# Environment management
uv venv                         # Create virtual environment
uv pip freeze                   # List installed packages
uv lock                         # Generate/update lock file
```

**Pro tips:**
- Use `uv run` for all Python executions to ensure correct environment
- `uv sync` automatically handles virtual environment creation
- Lock files ensure reproducible installations across machines

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Set up development environment with `uv sync && uv pip install -e .`
4. Make your changes
5. Run quality checks: `uv run ruff format . && uv run ruff check --fix .`
6. Test with `uv run python main.py`
7. Commit and push your changes
8. Submit a pull request

## Continuous Integration

The project uses GitHub Actions for automated testing and quality checks:

- **Code Quality**: Runs `ruff` linting and formatting checks
- **Testing**: Validates the stabilization pipeline with sample video
- **Multi-platform**: Tests on Linux, macOS, and Windows
- **Python Versions**: Tests against Python 3.11+

All pull requests must pass these checks before merging.

## Fast-Stab Integration

The FastStabilizer is inspired by the "Fast Full-frame Video Stabilization with Iterative Optimization" paper but adapted for real-time processing without deep learning dependencies. Key features:

### Technical Implementation
- **Optical Flow**: Supports both Lucas-Kanade (sparse) and Farneback (dense) methods
- **Confidence Mapping**: Generates confidence scores for flow vectors based on gradient consistency and flow magnitude
- **Homography Estimation**: Uses RANSAC-based homography estimation for robust motion modeling
- **Adaptive Smoothing**: Adjusts temporal smoothing based on motion confidence levels

### Performance on Mac M3
- Optimized for Apple Silicon ARM64 architecture
- Uses Accelerate framework through NumPy for matrix operations
- Compatible with Metal GPU acceleration where available
- Typical performance: 15-30ms per frame depending on resolution and flow method

### Usage Recommendations
- **Lucas-Kanade**: Better for videos with distinct features, lower computational cost
- **Farneback**: Better for videos with fine details, higher computational cost but more robust
- **Confidence Threshold**: 0.6 for stable footage, 0.4 for challenging conditions
- **Alpha (Smoothing)**: 0.9 for very smooth results, 0.7-0.8 for faster response