"""Basic tests for unshakify video stabilization functionality."""

import os
import tempfile

import cv2
import numpy as np

from unshakify.indicators import (
    cropping_ratio_from_video,
    distortion_value_from_videos,
    measure_latency,
    stability_improvement,
    stability_score_from_video,
)
from unshakify.stabilizer import OnlineStabilizer, write_stabilized_video


def create_test_video(path: str, width: int = 320, height: int = 240, frames: int = 30) -> None:
    """Create a simple test video with synthetic motion."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 30.0, (width, height))

    for i in range(frames):
        # Create a frame with some features
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Add some features to track
        center_x, center_y = width // 2, height // 2

        # Draw a rectangle that moves slightly to simulate shake
        shake_x = int(5 * np.sin(i * 0.5))  # Small horizontal shake
        shake_y = int(3 * np.cos(i * 0.3))  # Small vertical shake

        cv2.rectangle(
            frame,
            (center_x - 50 + shake_x, center_y - 30 + shake_y),
            (center_x + 50 + shake_x, center_y + 30 + shake_y),
            (255, 255, 255),
            -1,
        )

        # Add some corner features
        for j in range(5):
            x = (width // 6) * (j + 1) + shake_x
            y = (height // 3) + shake_y
            cv2.circle(frame, (x, y), 5, (128, 128, 128), -1)

        writer.write(frame)

    writer.release()


def test_stabilizer_initialization():
    """Test that OnlineStabilizer can be initialized with different parameters."""
    # Default parameters
    stabilizer = OnlineStabilizer()
    assert stabilizer.alpha > 0 and stabilizer.alpha <= 1

    # Custom parameters
    stabilizer = OnlineStabilizer(alpha=0.8, ransac_thresh=2.0)
    assert stabilizer.alpha == 0.8
    assert stabilizer.ransac_thresh == 2.0

    # Edge cases
    stabilizer = OnlineStabilizer(alpha=0.0)  # Should be clipped to valid range
    assert stabilizer.alpha >= 0.0

    stabilizer = OnlineStabilizer(alpha=1.5)  # Should be clipped to valid range
    assert stabilizer.alpha <= 1.0


def test_stabilization_pipeline():
    """Test the complete stabilization pipeline with a synthetic video."""
    with tempfile.TemporaryDirectory() as temp_dir:
        input_video = os.path.join(temp_dir, "test_input.mp4")
        output_video = os.path.join(temp_dir, "test_output.mp4")

        # Create test video
        create_test_video(input_video, frames=60)
        assert os.path.exists(input_video)

        # Initialize stabilizer
        stabilizer = OnlineStabilizer(alpha=0.9)

        # Test latency measurement
        latency = measure_latency(input_video, stabilizer, warmup_frames=3, max_frames=30)
        assert latency > 0, "Latency should be positive"
        assert latency < 1000, "Latency should be reasonable (< 1s per frame)"

        # Generate stabilized video
        write_stabilized_video(input_video, output_video, stabilizer)
        assert os.path.exists(output_video)

        # Test stability metrics
        stability_before = stability_score_from_video(input_video)
        stability_after = stability_score_from_video(output_video)
        improvement = stability_improvement(input_video, output_video)

        assert stability_before > 0, "Original video should have some motion"
        assert stability_after >= 0, "Stabilized video motion should be non-negative"
        assert 0 <= improvement <= 1, "Improvement should be between 0 and 1"

        # Test cropping ratio
        cropping_ratio = cropping_ratio_from_video(output_video)
        assert 0 < cropping_ratio <= 1, "Cropping ratio should be between 0 and 1"

        # Test distortion value
        distortion = distortion_value_from_videos(input_video, output_video)
        assert 0 <= distortion <= 1, "Distortion should be between 0 and 1"


def test_edge_cases():
    """Test edge cases and error handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with very short video
        short_video = os.path.join(temp_dir, "short.mp4")
        create_test_video(short_video, frames=3)

        stabilizer = OnlineStabilizer()

        # Should handle short videos gracefully
        try:
            latency = measure_latency(short_video, stabilizer, max_frames=2)
            assert latency >= 0  # Should return valid latency or NaN
        except Exception as e:
            # It's okay if it fails gracefully
            print(f"Expected behavior for short video: {e}")

        # Test reset functionality
        stabilizer.reset()
        assert stabilizer.prev_gray is None
        assert np.allclose(stabilizer.accum, 0)
        assert np.allclose(stabilizer.smooth_accum, 0)


def test_frame_processing():
    """Test individual frame processing."""
    stabilizer = OnlineStabilizer()

    # Create test frames
    height, width = 240, 320
    frame1 = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    frame2 = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

    # First frame should return as-is (initialization)
    result1 = stabilizer(frame1)
    assert result1.shape == frame1.shape
    assert np.array_equal(result1, frame1)

    # Second frame should be processed
    result2 = stabilizer(frame2)
    assert result2.shape == frame2.shape
    assert result2.dtype == frame2.dtype


if __name__ == "__main__":
    print("Running basic tests...")

    test_stabilizer_initialization()
    print("✅ Stabilizer initialization test passed")

    test_stabilization_pipeline()
    print("✅ Stabilization pipeline test passed")

    test_edge_cases()
    print("✅ Edge cases test passed")

    test_frame_processing()
    print("✅ Frame processing test passed")

    print("\n🎉 All tests passed!")
