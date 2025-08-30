#!/usr/bin/env python3
"""
Simple test script to verify Fast-Stab inspired stabilizer works on Mac M3.

This script performs basic functionality tests without requiring the sample video,
making it easier to verify the implementation works correctly.
"""

import cv2
import numpy as np
import time
from pathlib import Path
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unshakify.fast_stabilizer import FastStabilizer
from unshakify.stabilizer import OnlineStabilizer


def create_test_frames(num_frames=10, width=640, height=480):
    """Create synthetic test frames with simulated camera shake."""
    frames = []

    for i in range(num_frames):
        # Create a frame with some patterns
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Add some geometric patterns
        cv2.rectangle(frame, (100, 100), (200, 200), (0, 255, 0), 2)
        cv2.circle(frame, (300, 300), 50, (255, 0, 0), 2)
        cv2.line(frame, (0, i*10), (width, height - i*10), (0, 0, 255), 2)

        # Add some text
        cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Simulate camera shake by adding random translation
        shake_x = int(np.random.normal(0, 5))
        shake_y = int(np.random.normal(0, 5))

        # Apply transformation matrix for shake
        M = np.float32([[1, 0, shake_x], [0, 1, shake_y]])
        frame = cv2.warpAffine(frame, M, (width, height))

        frames.append(frame)

    return frames


def test_stabilizer_initialization():
    """Test stabilizer initialization."""
    print("Testing stabilizer initialization...")

    try:
        # Test FastStabilizer with different parameters
        fast_stab1 = FastStabilizer(flow_method="lucas_kanade")
        fast_stab2 = FastStabilizer(flow_method="farneback")

        # Test OnlineStabilizer
        basic_stab = OnlineStabilizer()

        print("  ✓ All stabilizers initialized successfully")
        return True
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return False


def test_basic_processing():
    """Test basic frame processing."""
    print("Testing basic frame processing...")

    try:
        frames = create_test_frames(5)

        # Test FastStabilizer with Lucas-Kanade
        fast_stab_lk = FastStabilizer(flow_method="lucas_kanade", confidence_threshold=0.3)
        fast_stab_lk.reset()

        processed_frames_lk = []
        for frame in frames:
            result = fast_stab_lk(frame)
            processed_frames_lk.append(result)
            assert result.shape == frame.shape, "Output frame shape mismatch"

        info = fast_stab_lk.get_stabilization_info()
        print(f"    Lucas-Kanade: avg_confidence={info['avg_confidence']:.3f}, transform_norm={info['transform_norm']:.3f}")

        # Test FastStabilizer with Farneback
        fast_stab_fb = FastStabilizer(flow_method="farneback", confidence_threshold=0.3)
        fast_stab_fb.reset()

        processed_frames_fb = []
        for frame in frames:
            result = fast_stab_fb(frame)
            processed_frames_fb.append(result)
            assert result.shape == frame.shape, "Output frame shape mismatch"

        info = fast_stab_fb.get_stabilization_info()
        print(f"    Farneback: avg_confidence={info['avg_confidence']:.3f}, transform_norm={info['transform_norm']:.3f}")

        # Test basic OnlineStabilizer for comparison
        basic_stab = OnlineStabilizer()
        basic_stab.reset()

        processed_frames_basic = []
        for frame in frames:
            result = basic_stab(frame)
            processed_frames_basic.append(result)
            assert result.shape == frame.shape, "Output frame shape mismatch"

        print("  ✓ Basic processing successful for all stabilizers")
        return True

    except Exception as e:
        print(f"  ✗ Basic processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Test processing performance."""
    print("Testing processing performance...")

    try:
        frames = create_test_frames(20)  # More frames for performance test

        methods = [
            ("OnlineStabilizer", OnlineStabilizer()),
            ("FastStabilizer (LK)", FastStabilizer(flow_method="lucas_kanade")),
            ("FastStabilizer (FB)", FastStabilizer(flow_method="farneback"))
        ]

        for name, stabilizer in methods:
            stabilizer.reset()

            start_time = time.time()
            for frame in frames:
                _ = stabilizer(frame)
            end_time = time.time()

            total_time = end_time - start_time
            fps = len(frames) / total_time
            ms_per_frame = (total_time / len(frames)) * 1000

            print(f"    {name}: {ms_per_frame:.2f} ms/frame ({fps:.1f} FPS)")

        print("  ✓ Performance testing completed")
        return True

    except Exception as e:
        print(f"  ✗ Performance testing failed: {e}")
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("Testing edge cases...")

    try:
        # Test with single frame (should not crash)
        frame = create_test_frames(1)[0]

        stabilizers = [
            OnlineStabilizer(),
            FastStabilizer(flow_method="lucas_kanade"),
            FastStabilizer(flow_method="farneback")
        ]

        for stabilizer in stabilizers:
            result = stabilizer(frame)
            assert result.shape == frame.shape, "Single frame processing failed"

        # Test with very small frames
        small_frame = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        for stabilizer in stabilizers:
            stabilizer.reset()
            result = stabilizer(small_frame)
            assert result.shape == small_frame.shape, "Small frame processing failed"

        # Test with uniform frames (no features)
        uniform_frame = np.ones((200, 200, 3), dtype=np.uint8) * 128
        for stabilizer in stabilizers:
            stabilizer.reset()
            result = stabilizer(uniform_frame)
            assert result.shape == uniform_frame.shape, "Uniform frame processing failed"

        print("  ✓ Edge case testing successful")
        return True

    except Exception as e:
        print(f"  ✗ Edge case testing failed: {e}")
        return False


def check_opencv_version():
    """Check OpenCV version and available features."""
    print(f"OpenCV version: {cv2.__version__}")

    # Check if we have the required functions
    required_functions = [
        'calcOpticalFlowPyrLK',
        'calcOpticalFlowFarneback',
        'goodFeaturesToTrack',
        'findHomography',
        'warpPerspective'
    ]

    missing_functions = []
    for func_name in required_functions:
        if not hasattr(cv2, func_name):
            missing_functions.append(func_name)

    if missing_functions:
        print(f"  ⚠️  Missing functions: {missing_functions}")
        return False
    else:
        print("  ✓ All required OpenCV functions available")
        return True


def main():
    """Run all tests."""
    print("=== Fast-Stab Compatibility Test for Mac M3 ===\n")

    # Check system info
    print(f"Python version: {sys.version}")
    opencv_ok = check_opencv_version()
    print()

    if not opencv_ok:
        print("❌ OpenCV compatibility issues detected")
        return False

    # Run tests
    tests = [
        test_stabilizer_initialization,
        test_basic_processing,
        test_performance,
        test_edge_cases
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    # Summary
    print("=== Test Summary ===")
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("🎉 All tests passed! Fast-Stab stabilizer is working correctly on your Mac M3.")
        print("\nYou can now run the demo with:")
        print("  python demo_fast_stab.py")
        return True
    else:
        print("❌ Some tests failed. Check the error messages above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
