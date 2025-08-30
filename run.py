#!/usr/bin/env python3
"""
UV-powered runner script for Unshakify video stabilization.

This script provides easy access to all main functionality using uv:
- Run main comparison demo
- Run tests
- Run advanced demos
- Quick setup checks
- uv environment management
"""

import sys
import subprocess
import argparse
import shutil
from pathlib import Path


def check_uv_available():
    """Check if uv is available and recommend installation if not."""
    if not shutil.which("uv"):
        print("❌ uv is not available!")
        print("This project is optimized for uv (10-100x faster than pip).")
        print("\nInstall uv:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("  # or on Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("  # or with pip: pip install uv")
        print("\nAfter installation, restart your terminal and try again.")
        return False
    return True


def run_with_uv(script_path):
    """Run a script using uv run for proper environment management."""
    return subprocess.run(["uv", "run", "python", script_path])


def run_main():
    """Run the main stabilization comparison demo."""
    print("🚀 Running main stabilization comparison with uv...")
    return run_with_uv("main.py")


def run_tests():
    """Run compatibility tests."""
    print("🧪 Running compatibility tests with uv...")
    return run_with_uv("tests/test_fast_stab.py")


def run_advanced_demo():
    """Run advanced comparison demo."""
    print("🔬 Running advanced demo with uv...")
    return run_with_uv("tests/demo_fast_stab.py")


def run_setup():
    """Run Mac M3 setup script."""
    print("⚙️ Running Mac M3 setup with uv...")
    return run_with_uv("setup_mac_m3.py")


def run_pytest():
    """Run full test suite with pytest."""
    print("🧪 Running pytest test suite with uv...")
    return subprocess.run(["uv", "run", "pytest", "tests/"])


def setup_environment():
    """Setup the uv environment."""
    print("📦 Setting up uv environment...")
    try:
        # Sync the environment
        result = subprocess.run(["uv", "sync"], check=True)
        print("✅ Environment setup complete")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Environment setup failed: {e}")
        return e


def show_status():
    """Show project and environment status."""
    print("📊 Project Status:")

    # Check uv version
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=True)
        print(f"  ✅ uv: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ uv: not available")

    # Check if virtual environment is active
    try:
        result = subprocess.run(["uv", "run", "python", "-c", "import sys; print(sys.prefix)"],
                              capture_output=True, text=True, check=True)
        venv_path = result.stdout.strip()
        print(f"  ✅ Virtual environment: {Path(venv_path).name}")
    except subprocess.CalledProcessError:
        print("  ⚠️  Virtual environment: not detected")

    # Check if packages are installed
    try:
        subprocess.run(["uv", "run", "python", "-c", "import unshakify"],
                      check=True, capture_output=True)
        print("  ✅ unshakify: installed")
    except subprocess.CalledProcessError:
        print("  ❌ unshakify: not installed (run setup)")

    # Check for sample video
    video_path = Path("raw.mp4")
    if video_path.exists():
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Sample video: raw.mp4 ({size_mb:.1f} MB)")
    else:
        print("  ⚠️  Sample video: raw.mp4 not found")


def check_video():
    """Check if sample video exists."""
    video_path = Path("raw.mp4")
    if video_path.exists():
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"✅ Sample video found: raw.mp4 ({size_mb:.1f} MB)")
        return True
    else:
        print("❌ Sample video 'raw.mp4' not found!")
        print("Please place a video file named 'raw.mp4' in the current directory.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Unshakify Video Stabilization Runner (UV-Powered)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python run.py                    # Run main comparison demo
  uv run python run.py --test             # Run compatibility tests
  uv run python run.py --demo             # Run advanced demo
  uv run python run.py --setup            # Run Mac M3 setup
  uv run python run.py --pytest           # Run full test suite
  uv run python run.py --env-setup        # Setup uv environment
  uv run python run.py --status           # Show project status

Note: This script is optimized for uv. Install with:
  curl -LsSf https://astral.sh/uv/install.sh | sh
        """
    )

    parser.add_argument(
        "--test", action="store_true",
        help="Run compatibility tests"
    )

    parser.add_argument(
        "--demo", action="store_true",
        help="Run advanced comparison demo"
    )

    parser.add_argument(
        "--setup", action="store_true",
        help="Run Mac M3 setup script"
    )

    parser.add_argument(
        "--check", action="store_true",
        help="Check if sample video exists"
    )

    parser.add_argument(
        "--pytest", action="store_true",
        help="Run full pytest test suite"
    )

    parser.add_argument(
        "--env-setup", action="store_true",
        help="Setup uv environment (sync dependencies)"
    )

    parser.add_argument(
        "--status", action="store_true",
        help="Show project and environment status"
    )

    args = parser.parse_args()

    # Check uv availability first
    if not check_uv_available():
        sys.exit(1)

    # If no arguments, run main demo
    if not any([args.test, args.demo, args.setup, args.check, args.pytest, args.env_setup, args.status]):
        if not check_video():
            sys.exit(1)
        result = run_main()
        sys.exit(result.returncode)

    # Handle specific commands
    if args.status:
        show_status()
        sys.exit(0)

    if args.env_setup:
        result = setup_environment()
        sys.exit(result.returncode if hasattr(result, 'returncode') else 0)

    if args.check:
        success = check_video()
        sys.exit(0 if success else 1)

    if args.setup:
        result = run_setup()
        sys.exit(result.returncode)

    if args.test:
        result = run_tests()
        sys.exit(result.returncode)

    if args.pytest:
        result = run_pytest()
        sys.exit(result.returncode)

    if args.demo:
        if not check_video():
            sys.exit(1)
        result = run_advanced_demo()
        sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error: {e}")
        print("\nIf you're having issues:")
        print("• Ensure uv is installed: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("• Try setting up the environment: uv run python run.py --env-setup")
        print("• Check project status: uv run python run.py --status")
        sys.exit(1)
