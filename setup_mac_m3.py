#!/usr/bin/env python3
"""
Setup script for Mac M3 (Apple Silicon) compatibility.

This script helps set up the Fast-Stab inspired video stabilizer on Mac M3,
ensuring optimal performance and compatibility.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def print_header():
    """Print setup header."""
    print("🍎 Unshakify Fast-Stab Setup for Mac M3 (Apple Silicon)")
    print("=" * 60)


def check_system_requirements():
    """Check if running on Apple Silicon Mac."""
    print("\n1. Checking system requirements...")

    # Check if running on macOS
    if platform.system() != "Darwin":
        print("   ❌ This setup script is designed for macOS")
        return False

    # Check if running on Apple Silicon
    try:
        # Check architecture
        arch = platform.machine()
        if arch != "arm64":
            print(f"   ⚠️  Running on {arch} (expected arm64 for M-series chips)")
            print("   This setup is optimized for Apple Silicon (M1/M2/M3)")
        else:
            print("   ✅ Apple Silicon (ARM64) detected")

        # Check macOS version
        macos_version = platform.mac_ver()[0]
        print(f"   ✅ macOS version: {macos_version}")

        return True
    except Exception as e:
        print(f"   ❌ Error checking system: {e}")
        return False


def check_python_version():
    """Check Python version compatibility."""
    print("\n2. Checking Python version...")

    version = sys.version_info
    if version.major != 3 or version.minor < 11:
        print(f"   ❌ Python {version.major}.{version.minor} detected")
        print("   Python 3.11+ is required")
        return False

    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_brew_and_ffmpeg():
    """Check for Homebrew and FFmpeg installation."""
    print("\n3. Checking multimedia dependencies...")

    # Check for brew
    try:
        result = subprocess.run(['brew', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Homebrew is installed")

            # Check for FFmpeg
            result = subprocess.run(['brew', 'list', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ FFmpeg is installed")
            else:
                print("   ⚠️  FFmpeg not found via Homebrew")
                print("   Installing FFmpeg for better video codec support...")
                try:
                    subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
                    print("   ✅ FFmpeg installed successfully")
                except subprocess.CalledProcessError:
                    print("   ❌ Failed to install FFmpeg")
                    print("   You can install it manually: brew install ffmpeg")

    except FileNotFoundError:
        print("   ⚠️  Homebrew not found")
        print("   Consider installing Homebrew for easier dependency management:")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")


def install_python_dependencies():
    """Install Python dependencies optimized for Mac M3."""
    print("\n4. Installing Python dependencies...")

    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("   ⚠️  Not in a virtual environment")
        print("   Recommended: create a virtual environment first:")
        print("   python -m venv .venv && source .venv/bin/activate")

        response = input("   Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            print("   Setup cancelled")
            return False
    else:
        print("   ✅ Virtual environment detected")

    # Check for uv (required package manager)
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, check=True, text=True)
        uv_version = result.stdout.strip()
        print(f"   ✅ uv package manager available: {uv_version}")
        use_uv = True
    except FileNotFoundError:
        print("   ❌ uv package manager not found")
        print("   uv is required for this setup. Please install it first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   # or on Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("   # or with pip: pip install uv")
        return False
    except subprocess.CalledProcessError:
        print("   ❌ uv found but not working properly")
        return False

    # Install dependencies using uv
    try:
        print("   📦 Installing project with uv...")

        # First, sync/create the virtual environment if needed
        print("   Creating/syncing virtual environment...")
        subprocess.run(['uv', 'sync'], check=True)
        print("   ✅ Virtual environment ready")

        # Install main dependencies with Mac M3 optimizations
        cmd = ['uv', 'pip', 'install', '-e', '.[mac-m3,dev]']
        print(f"   Installing optimized dependencies: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        print("   ✅ All dependencies installed successfully with uv")
        return True

    except subprocess.CalledProcessError as e:
        print(f"   ❌ uv installation failed: {e}")
        print("   This might be due to:")
        print("   • Network connectivity issues")
        print("   • Missing system dependencies")
        print("   • Incompatible Python version")
        print("   Please check the error above and try again.")
        return False


def run_compatibility_test():
    """Run compatibility test."""
    print("\n5. Running compatibility test...")

    try:
        result = subprocess.run([sys.executable, 'tests/test_fast_stab.py'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("   ✅ All compatibility tests passed!")
            return True
        else:
            print("   ❌ Some tests failed:")
            print(result.stdout)
            if result.stderr:
                print("   Errors:")
                print(result.stderr)
            return False

    except FileNotFoundError:
        print("   ❌ tests/test_fast_stab.py not found")
        return False
    except Exception as e:
        print(f"   ❌ Test execution failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("\n1. Test the stabilizers (main comparison):")
    print("   uv run python main.py")
    print("\n2. Test the Fast-Stab inspired stabilizer:")
    print("   uv run python tests/demo_fast_stab.py")
    print("\n3. Run compatibility tests anytime:")
    print("   uv run python tests/test_fast_stab.py")
    print("\n4. Use the simple runner:")
    print("   uv run python run.py")

    print("\n💡 Tips for Mac M3:")
    print("• OpenCV will automatically use optimized ARM64 builds")
    print("• NumPy will leverage the Accelerate framework")
    print("• uv provides 10-100x faster package management than pip")
    print("• Use 'uv run' to execute scripts in the managed environment")
    print("• Monitor Activity Monitor for GPU usage during processing")

    print("\n🔧 Troubleshooting:")
    print("• If video playback issues occur, ensure FFmpeg is installed")
    print("• For performance issues, check that you're using ARM64 Python")
    print("• Use 'uv run python -c \"import platform; print(platform.machine())\"' to verify")
    print("• If uv commands fail, ensure you're in the project directory")
    print("• Use 'uv --help' for uv-specific troubleshooting")


def main():
    """Main setup function."""
    print_header()

    # Run all setup steps
    steps = [
        ("System Requirements", check_system_requirements),
        ("Python Version", check_python_version),
        ("Multimedia Dependencies", check_brew_and_ffmpeg),
        ("Python Dependencies", install_python_dependencies),
        ("Compatibility Test", run_compatibility_test),
    ]

    failed_steps = []

    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except KeyboardInterrupt:
            print(f"\n\n❌ Setup interrupted during: {step_name}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)

    # Summary
    if not failed_steps:
        print_next_steps()
        return True
    else:
        print(f"\n❌ Setup completed with issues in: {', '.join(failed_steps)}")
        print("\nPlease address the issues above and run setup again.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(1)
