#!/usr/bin/env python3
"""
Demo script comparing the original OnlineStabilizer with the new FastStabilizer.

This script demonstrates:
1. Basic stabilization with OnlineStabilizer
2. Advanced stabilization with FastStabilizer (Fast-Stab inspired)
3. Performance comparison between both methods
4. Quality metrics evaluation
"""

import time
from pathlib import Path
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unshakify.stabilizer import OnlineStabilizer, write_stabilized_video
from unshakify.fast_stabilizer import FastStabilizer, write_fast_stabilized_video
from unshakify.indicators import (
    measure_latency,
    stability_score_from_video,
    stability_improvement,
    cropping_ratio_from_video,
    distortion_value_from_videos,
)


def demo_comparison():
    """Compare original and Fast-Stab inspired stabilizers."""

    # Input video path
    raw_video = "raw.mp4"
    if not Path(raw_video).exists():
        print(f"Error: {raw_video} not found. Please ensure the sample video exists.")
        return

    # Output video paths
    basic_output = "stab_basic.mp4"
    fast_output = "stab_fast.mp4"

    print("=== Unshakify Stabilizer Comparison Demo ===\n")

    # 1. Basic OnlineStabilizer
    print("1. Testing Basic OnlineStabilizer...")
    basic_stabilizer = OnlineStabilizer(alpha=0.90)

    start_time = time.time()
    basic_latency = measure_latency(raw_video, basic_stabilizer, warmup_frames=5, max_frames=300)
    write_stabilized_video(raw_video, basic_output, basic_stabilizer, fourcc="mp4v")
    basic_time = time.time() - start_time

    print(f"   ✓ Basic stabilization completed in {basic_time:.2f}s")
    print(f"   ✓ Processing latency: {basic_latency:.2f} ms/frame")

    # 2. Fast-Stab inspired FastStabilizer
    print("\n2. Testing FastStabilizer (Fast-Stab inspired)...")

    # Test both flow methods
    for flow_method in ["lucas_kanade", "farneback"]:
        output_file = f"stab_fast_{flow_method}.mp4"
        print(f"\n   Testing {flow_method} flow method...")

        fast_stabilizer = FastStabilizer(
            alpha=0.85,
            flow_method=flow_method,
            confidence_threshold=0.6,
            min_flow_points=500,
            max_corners=1000,
            quality_level=0.01,
            min_distance=10
        )

        start_time = time.time()
        try:
            fast_latency = measure_latency(raw_video, fast_stabilizer, warmup_frames=5, max_frames=300)
            write_fast_stabilized_video(raw_video, output_file, fast_stabilizer, fourcc="mp4v")
            fast_time = time.time() - start_time

            print(f"     ✓ Fast stabilization ({flow_method}) completed in {fast_time:.2f}s")
            print(f"     ✓ Processing latency: {fast_latency:.2f} ms/frame")

            # Get stabilization info
            info = fast_stabilizer.get_stabilization_info()
            print(f"     ✓ Average confidence: {info['avg_confidence']:.3f}")
            print(f"     ✓ Transform norm: {info['transform_norm']:.3f}")

        except Exception as e:
            print(f"     ✗ Error with {flow_method}: {str(e)}")
            continue

    # 3. Quality Analysis
    print("\n3. Quality Analysis...")

    def analyze_video(video_path, name):
        """Analyze video quality metrics."""
        if not Path(video_path).exists():
            print(f"   ✗ {name}: Video file not found")
            return None

        try:
            S_before = stability_score_from_video(raw_video)
            S_after = stability_score_from_video(video_path)
            S_improvement = stability_improvement(raw_video, video_path)
            cropping_ratio = cropping_ratio_from_video(video_path)
            distortion_value = distortion_value_from_videos(raw_video, video_path)

            print(f"   {name}:")
            print(f"     • Stability before: {S_before:.3f}")
            print(f"     • Stability after:  {S_after:.3f}")
            print(f"     • Improvement:      {S_improvement:.3f} (higher is better)")
            print(f"     • Cropping ratio:   {cropping_ratio:.3f} (1.0 = no crop)")
            print(f"     • Distortion:       {distortion_value:.3f} (lower is better)")

            return {
                'improvement': S_improvement,
                'cropping': cropping_ratio,
                'distortion': distortion_value
            }
        except Exception as e:
            print(f"   ✗ {name}: Error computing metrics - {str(e)}")
            return None

    basic_metrics = analyze_video(basic_output, "Basic Stabilizer")

    # Analyze Fast stabilizer outputs
    fast_metrics = {}
    for flow_method in ["lucas_kanade", "farneback"]:
        output_file = f"stab_fast_{flow_method}.mp4"
        metrics = analyze_video(output_file, f"Fast Stabilizer ({flow_method})")
        if metrics:
            fast_metrics[flow_method] = metrics

    # 4. Summary and Recommendations
    print("\n4. Summary and Recommendations...")
    print("=" * 50)

    if basic_metrics and fast_metrics:
        print("Performance Comparison:")
        print(f"• Basic Stabilizer:")
        print(f"  - Improvement: {basic_metrics['improvement']:.3f}")
        print(f"  - Cropping:    {basic_metrics['cropping']:.3f}")
        print(f"  - Distortion:  {basic_metrics['distortion']:.3f}")

        for method, metrics in fast_metrics.items():
            print(f"• Fast Stabilizer ({method}):")
            print(f"  - Improvement: {metrics['improvement']:.3f}")
            print(f"  - Cropping:    {metrics['cropping']:.3f}")
            print(f"  - Distortion:  {metrics['distortion']:.3f}")

        # Find best method
        all_methods = [("Basic", basic_metrics)]
        all_methods.extend([(f"Fast ({k})", v) for k, v in fast_metrics.items()])

        best_stability = max(all_methods, key=lambda x: x[1]['improvement'])
        best_quality = min(all_methods, key=lambda x: x[1]['distortion'])
        best_cropping = max(all_methods, key=lambda x: x[1]['cropping'])

        print(f"\nRecommendations:")
        print(f"• Best stability improvement: {best_stability[0]}")
        print(f"• Best quality (low distortion): {best_quality[0]}")
        print(f"• Best cropping ratio: {best_cropping[0]}")

    print("\nDemo completed! Check the generated video files:")
    print(f"• {basic_output} - Basic stabilizer output")
    for flow_method in ["lucas_kanade", "farneback"]:
        output_file = f"stab_fast_{flow_method}.mp4"
        if Path(output_file).exists():
            print(f"• {output_file} - Fast stabilizer ({flow_method}) output")


def demo_fast_stabilizer_features():
    """Demonstrate specific Fast-Stab features."""
    print("\n=== FastStabilizer Advanced Features Demo ===\n")

    raw_video = "raw.mp4"
    if not Path(raw_video).exists():
        print(f"Error: {raw_video} not found.")
        return

    # Test different configurations
    configs = [
        {
            "name": "Conservative (High Confidence)",
            "params": {
                "alpha": 0.95,
                "confidence_threshold": 0.8,
                "flow_method": "lucas_kanade"
            }
        },
        {
            "name": "Balanced",
            "params": {
                "alpha": 0.85,
                "confidence_threshold": 0.6,
                "flow_method": "lucas_kanade"
            }
        },
        {
            "name": "Aggressive (Low Latency)",
            "params": {
                "alpha": 0.7,
                "confidence_threshold": 0.4,
                "flow_method": "farneback"
            }
        }
    ]

    for i, config in enumerate(configs):
        print(f"{i+1}. Testing {config['name']} configuration...")

        stabilizer = FastStabilizer(**config['params'])
        output_file = f"stab_config_{i+1}.mp4"

        try:
            start_time = time.time()
            write_fast_stabilized_video(raw_video, output_file, stabilizer, limit_frames=100)
            process_time = time.time() - start_time

            info = stabilizer.get_stabilization_info()
            print(f"   ✓ Processing time: {process_time:.2f}s for 100 frames")
            print(f"   ✓ Average confidence: {info['avg_confidence']:.3f}")
            print(f"   ✓ Transform complexity: {info['transform_norm']:.3f}")

            # Quick quality check
            if Path(output_file).exists():
                improvement = stability_improvement(raw_video, output_file)
                print(f"   ✓ Stability improvement: {improvement:.3f}")

        except Exception as e:
            print(f"   ✗ Error: {str(e)}")

        print()


if __name__ == "__main__":
    try:
        # Run main comparison demo
        demo_comparison()

        # Run advanced features demo
        demo_fast_stabilizer_features()

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Demo failed with error: {str(e)}")
        print("Make sure you have the required sample video 'raw.mp4' in the current directory.")
