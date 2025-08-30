#!/usr/bin/env python3
"""
Unshakify Main Demo - Video Stabilization Comparison

This script demonstrates and compares the performance of both stabilizers:
1. OnlineStabilizer (Basic KLT-based stabilizer)
2. FastStabilizer (Fast-Stab inspired with optical flow and confidence mapping)

The script processes the sample video with both methods and provides
comprehensive performance metrics and quality comparisons.
"""

import time
from pathlib import Path
import sys
from typing import Dict, Any, Optional

from unshakify.stabilizer import OnlineStabilizer, write_stabilized_video
from unshakify.fast_stabilizer import FastStabilizer, write_fast_stabilized_video
from unshakify.indicators import (
    measure_latency,
    stability_score_from_video,
    stability_improvement,
    cropping_ratio_from_video,
    distortion_value_from_videos,
)


def print_header():
    """Print the main header."""
    print("=" * 70)
    print("🎬 UNSHAKIFY - AI-BASED VIDEO STABILIZATION COMPARISON")
    print("=" * 70)
    print("Comparing OnlineStabilizer vs FastStabilizer performance")
    print()


def check_input_video(video_path: str) -> bool:
    """Check if input video exists."""
    if not Path(video_path).exists():
        print(f"❌ Error: Input video '{video_path}' not found.")
        print("Please ensure you have a video file named 'raw.mp4' in the current directory.")
        print("You can use any video file, just rename it to 'raw.mp4'")
        return False

    file_size = Path(video_path).stat().st_size / (1024 * 1024)  # Size in MB
    print(f"✅ Input video: {video_path} ({file_size:.1f} MB)")
    return True


def run_basic_stabilizer(input_video: str, max_frames: Optional[int] = None) -> Dict[str, Any]:
    """Run the basic OnlineStabilizer and return performance metrics."""
    print("\n1️⃣  RUNNING BASIC ONLINE STABILIZER")
    print("-" * 50)

    output_video = "stab_basic.mp4"

    # Initialize stabilizer
    stabilizer = OnlineStabilizer(alpha=0.90)

    try:
        # Measure processing latency
        print("📊 Measuring processing latency...")
        start_time = time.time()
        latency = measure_latency(input_video, stabilizer, warmup_frames=5, max_frames=300)
        latency_time = time.time() - start_time
        print(f"   ⏱️  Latency measurement: {latency:.2f} ms/frame (took {latency_time:.1f}s)")

        # Generate stabilized video
        print("🎥 Processing full video...")
        start_time = time.time()
        write_stabilized_video(input_video, output_video, stabilizer,
                             fourcc="mp4v", limit_frames=max_frames)
        process_time = time.time() - start_time
        print(f"   ✅ Video processing completed in {process_time:.1f}s")

        # Calculate quality metrics
        print("📈 Computing quality metrics...")
        metrics_start = time.time()

        S_before = stability_score_from_video(input_video)
        S_after = stability_score_from_video(output_video)
        improvement = stability_improvement(input_video, output_video)
        cropping = cropping_ratio_from_video(output_video)
        distortion = distortion_value_from_videos(input_video, output_video)

        metrics_time = time.time() - metrics_start

        results = {
            'name': 'Basic OnlineStabilizer',
            'output_file': output_video,
            'latency_ms': latency,
            'process_time': process_time,
            'metrics_time': metrics_time,
            'stability_before': S_before,
            'stability_after': S_after,
            'improvement': improvement,
            'cropping_ratio': cropping,
            'distortion': distortion,
            'total_time': latency_time + process_time + metrics_time
        }

        print(f"   ✅ Quality metrics computed in {metrics_time:.1f}s")
        print(f"   📊 Results: {improvement:.3f} improvement, {cropping:.3f} cropping, {distortion:.3f} distortion")

        return results

    except Exception as e:
        print(f"   ❌ Basic stabilizer failed: {str(e)}")
        return {'name': 'Basic OnlineStabilizer', 'error': str(e)}


def run_fast_stabilizer(input_video: str, flow_method: str, max_frames: Optional[int] = None) -> Dict[str, Any]:
    """Run the FastStabilizer with specified flow method and return performance metrics."""
    method_name = flow_method.replace('_', '-').title()
    print(f"\n2️⃣  RUNNING FAST STABILIZER ({method_name})")
    print("-" * 50)

    output_video = f"stab_fast_{flow_method}.mp4"

    # Initialize FastStabilizer with optimized parameters
    stabilizer_params = {
        'alpha': 0.85,
        'flow_method': flow_method,
        'confidence_threshold': 0.6,
        'min_flow_points': 500,
        'max_corners': 1000,
        'quality_level': 0.01,
        'min_distance': 10
    }

    stabilizer = FastStabilizer(**stabilizer_params)

    try:
        # Measure processing latency
        print("📊 Measuring processing latency...")
        start_time = time.time()
        latency = measure_latency(input_video, stabilizer, warmup_frames=5, max_frames=300)
        latency_time = time.time() - start_time
        print(f"   ⏱️  Latency measurement: {latency:.2f} ms/frame (took {latency_time:.1f}s)")

        # Generate stabilized video
        print("🎥 Processing full video...")
        start_time = time.time()
        write_fast_stabilized_video(input_video, output_video, stabilizer,
                                   fourcc="mp4v", limit_frames=max_frames)
        process_time = time.time() - start_time
        print(f"   ✅ Video processing completed in {process_time:.1f}s")

        # Get stabilizer-specific metrics
        stab_info = stabilizer.get_stabilization_info()
        print(f"   📊 Stabilizer info: confidence={stab_info['avg_confidence']:.3f}, "
              f"transform_norm={stab_info['transform_norm']:.3f}")

        # Calculate quality metrics
        print("📈 Computing quality metrics...")
        metrics_start = time.time()

        S_before = stability_score_from_video(input_video)
        S_after = stability_score_from_video(output_video)
        improvement = stability_improvement(input_video, output_video)
        cropping = cropping_ratio_from_video(output_video)
        distortion = distortion_value_from_videos(input_video, output_video)

        metrics_time = time.time() - metrics_start

        results = {
            'name': f'FastStabilizer ({method_name})',
            'output_file': output_video,
            'flow_method': flow_method,
            'latency_ms': latency,
            'process_time': process_time,
            'metrics_time': metrics_time,
            'stability_before': S_before,
            'stability_after': S_after,
            'improvement': improvement,
            'cropping_ratio': cropping,
            'distortion': distortion,
            'avg_confidence': stab_info['avg_confidence'],
            'transform_norm': stab_info['transform_norm'],
            'total_time': latency_time + process_time + metrics_time
        }

        print(f"   ✅ Quality metrics computed in {metrics_time:.1f}s")
        print(f"   📊 Results: {improvement:.3f} improvement, {cropping:.3f} cropping, {distortion:.3f} distortion")

        return results

    except Exception as e:
        print(f"   ❌ Fast stabilizer ({method_name}) failed: {str(e)}")
        return {'name': f'FastStabilizer ({method_name})', 'flow_method': flow_method, 'error': str(e)}


def print_comparison_results(results: list):
    """Print comprehensive comparison of all stabilizer results."""
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE COMPARISON RESULTS")
    print("=" * 70)

    # Filter successful results
    successful_results = [r for r in results if 'error' not in r]
    failed_results = [r for r in results if 'error' in r]

    if not successful_results:
        print("❌ No stabilizers completed successfully!")
        return

    # Performance Summary Table
    print("\n📈 PERFORMANCE SUMMARY")
    print("-" * 70)
    print(f"{'Method':<25} {'Latency':<12} {'Total Time':<12} {'FPS':<8}")
    print("-" * 70)

    for result in successful_results:
        fps = 1000 / result['latency_ms'] if result['latency_ms'] > 0 else 0
        print(f"{result['name']:<25} "
              f"{result['latency_ms']:.1f} ms{'':<6} "
              f"{result['total_time']:.1f}s{'':<7} "
              f"{fps:.1f}")

    # Quality Metrics Table
    print(f"\n📊 QUALITY METRICS COMPARISON")
    print("-" * 70)
    print(f"{'Method':<25} {'Improvement':<12} {'Cropping':<10} {'Distortion':<12}")
    print("-" * 70)

    for result in successful_results:
        print(f"{result['name']:<25} "
              f"{result['improvement']:.3f}{'':<7} "
              f"{result['cropping_ratio']:.3f}{'':<5} "
              f"{result['distortion']:.3f}")

    # Fast Stabilizer Specific Metrics
    fast_results = [r for r in successful_results if 'FastStabilizer' in r['name']]
    if fast_results:
        print(f"\n🔬 FAST STABILIZER ANALYSIS")
        print("-" * 70)
        print(f"{'Method':<25} {'Confidence':<12} {'Transform Norm':<15}")
        print("-" * 70)

        for result in fast_results:
            print(f"{result['name']:<25} "
                  f"{result['avg_confidence']:.3f}{'':<7} "
                  f"{result['transform_norm']:.3f}")

    # Recommendations
    print(f"\n🏆 RECOMMENDATIONS")
    print("-" * 70)

    # Best performance
    best_perf = min(successful_results, key=lambda x: x['latency_ms'])
    print(f"🚀 Fastest processing: {best_perf['name']} ({best_perf['latency_ms']:.1f} ms/frame)")

    # Best quality (highest improvement)
    best_quality = max(successful_results, key=lambda x: x['improvement'])
    print(f"⭐ Best stabilization: {best_quality['name']} ({best_quality['improvement']:.3f} improvement)")

    # Best balance (improvement/latency ratio)
    best_balance = max(successful_results, key=lambda x: x['improvement'] / (x['latency_ms'] / 100))
    print(f"⚖️  Best balance: {best_balance['name']} (quality/speed ratio)")

    # Lowest distortion
    best_fidelity = min(successful_results, key=lambda x: x['distortion'])
    print(f"🎯 Best fidelity: {best_fidelity['name']} ({best_fidelity['distortion']:.3f} distortion)")

    # Usage recommendations
    print(f"\n💡 USAGE GUIDELINES")
    print("-" * 70)
    print("• For real-time applications: Choose fastest method")
    print("• For best quality: Choose method with highest improvement")
    print("• For handheld footage: FastStabilizer with Lucas-Kanade")
    print("• For drone/vehicle footage: FastStabilizer with Farneback")
    print("• For live streaming: Basic OnlineStabilizer")
    print("• For post-production: FastStabilizer with high confidence threshold")

    # Failed results
    if failed_results:
        print(f"\n⚠️  FAILED METHODS")
        print("-" * 70)
        for result in failed_results:
            print(f"❌ {result['name']}: {result['error']}")

    # Output files
    print(f"\n📁 OUTPUT FILES")
    print("-" * 70)
    for result in successful_results:
        file_path = Path(result['output_file'])
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ {result['output_file']} ({size_mb:.1f} MB)")
        else:
            print(f"❌ {result['output_file']} (not found)")


def main():
    """Main function to run stabilization comparison."""
    print_header()

    # Configuration
    input_video = "raw.mp4"
    max_frames = None  # Process full video, set to number to limit frames

    # Check input video
    if not check_input_video(input_video):
        sys.exit(1)

    # Run all stabilizers
    all_results = []

    # 1. Basic OnlineStabilizer
    try:
        basic_result = run_basic_stabilizer(input_video, max_frames)
        all_results.append(basic_result)
    except KeyboardInterrupt:
        print("\n❌ Basic stabilizer interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error in basic stabilizer: {e}")
        all_results.append({'name': 'Basic OnlineStabilizer', 'error': str(e)})

    # 2. FastStabilizer with Lucas-Kanade
    try:
        fast_lk_result = run_fast_stabilizer(input_video, "lucas_kanade", max_frames)
        all_results.append(fast_lk_result)
    except KeyboardInterrupt:
        print("\n❌ Fast stabilizer (Lucas-Kanade) interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error in fast stabilizer (Lucas-Kanade): {e}")
        all_results.append({'name': 'FastStabilizer (Lucas-Kanade)', 'flow_method': 'lucas_kanade', 'error': str(e)})

    # 3. FastStabilizer with Farneback
    try:
        fast_fb_result = run_fast_stabilizer(input_video, "farneback", max_frames)
        all_results.append(fast_fb_result)
    except KeyboardInterrupt:
        print("\n❌ Fast stabilizer (Farneback) interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error in fast stabilizer (Farneback): {e}")
        all_results.append({'name': 'FastStabilizer (Farneback)', 'flow_method': 'farneback', 'error': str(e)})

    # Print comprehensive comparison
    print_comparison_results(all_results)

    print(f"\n🎉 Comparison completed! Check the output videos for visual results.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please check that all dependencies are installed correctly.")
        sys.exit(1)
