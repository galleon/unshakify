# Unshakify - AI-Based Video Stabilization

Unshakify is a lightweight, real-time video stabilization system that computes key performance indicators for AI-based image stabilizers. It uses computer vision techniques to analyze camera motion, apply smoothing transformations, and measure the quality of stabilization results.

## Features

- **Real-time Processing**: Online stabilizer that processes frames sequentially with minimal latency
- **Motion Estimation**: Uses KLT (Kanade-Lucas-Tomasi) feature tracking and robust affine transformation estimation
- **Smooth Stabilization**: Applies exponential moving average (EMA) smoothing to camera motion paths
- **Comprehensive Metrics**: Computes multiple indicators to evaluate stabilization quality
- **Minimal Dependencies**: Only requires OpenCV and NumPy

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

### Using uv (Recommended - Fast!)

[uv](https://github.com/astral-sh/uv) is a blazing fast Python package manager written in Rust. It's significantly faster than pip and provides better dependency resolution.

**Benefits of using uv:**
- ⚡ **10-100x faster** than pip for installation
- 🔒 **Better dependency resolution** with lockfile support
- 🚀 **Built-in virtual environment management**
- 📦 **Drop-in replacement** for pip commands

```bash
# Install dependencies and create virtual environment
uv sync

# Install the package in development mode
uv pip install -e .
```

### Using pip (Traditional)

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the package:
```bash
pip install -e .
```

## Usage

### Basic Example

```python
from unshakify.stabilizer import OnlineStabilizer, write_stabilized_video
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

### Running the Demo

The project includes a demo script that processes the included sample video:

**Using uv (recommended):**
```bash
uv run python main.py
```

**Using traditional approach:**
```bash
# Make sure you're in the project directory and virtual environment is activated
source venv/bin/activate  # or .venv/bin/activate if using uv
python main.py
```

Expected output:
```
Latency: 20.15 ms/frame
Stability before: 29.530
Stability after : 28.564
Stability improvement: 0.033  (0–1, higher is better)
Cropping ratio: 0.998       (1.0 = no crop)
Distortion value: 0.365       (lower is better)
```

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

### Installing uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip
pip install uv
```

## Code Quality

This project uses `ruff` for fast Python linting and formatting:

```bash
# Check code quality
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

# Install in development mode with uv
uv sync
uv pip install -e .

# Run tests (if available)
uv run pytest

# Run the demo
uv run python main.py
```

### Development Commands

```bash
# Add new dependencies
uv add package-name

# Add development dependencies (ruff is already included)
uv add --dev pytest

# Update dependencies
uv sync --upgrade

# Run with specific Python version
uv run --python 3.11 python main.py

# Create production lockfile
uv lock

# Code quality checks
uv run ruff check .
uv run ruff format .
```

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