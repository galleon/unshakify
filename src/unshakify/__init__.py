"""Unshakify - AI-Based Video Stabilization with Performance Indicators."""

from .stabilizer import OnlineStabilizer, write_stabilized_video
from .fast_stabilizer import FastStabilizer, write_fast_stabilized_video
from .indicators import (
    measure_latency,
    stability_score_from_video,
    stability_improvement,
    cropping_ratio_from_video,
    distortion_value_from_videos,
)

__version__ = "0.1.0"
__all__ = [
    # Original stabilizer
    "OnlineStabilizer",
    "write_stabilized_video",
    # Fast-Stab inspired stabilizer
    "FastStabilizer",
    "write_fast_stabilized_video",
    # Performance indicators
    "measure_latency",
    "stability_score_from_video",
    "stability_improvement",
    "cropping_ratio_from_video",
    "distortion_value_from_videos",
]
