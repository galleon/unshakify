from unshakify.stabilizer import OnlineStabilizer, write_stabilized_video
from unshakify.indicators import (
    measure_latency,
    stability_score_from_video,
    stability_improvement,
    cropping_ratio_from_video,
    distortion_value_from_videos,
)

raw = "raw.mp4"
stab = "stab.mp4"

# 1) Measure latency of the callable (ms/frame)
stabilizer = OnlineStabilizer(alpha=0.90)
latency_ms = measure_latency(raw, stabilizer, warmup_frames=5, max_frames=300)
print(f"Latency: {latency_ms:.2f} ms/frame")

# 2) Produce a stabilized video using the same callable
write_stabilized_video(raw, stab, stabilizer, fourcc="mp4v")

# 3) Compute indicators
S_before = stability_score_from_video(raw)
S_after = stability_score_from_video(stab)
S_impr = stability_improvement(raw, stab)
C = cropping_ratio_from_video(stab)
D = distortion_value_from_videos(raw, stab)

print(f"Stability before: {S_before:.3f}")
print(f"Stability after : {S_after:.3f}")
print(f"Stability improv: {S_impr:.3f}  (0-1, higher is better)")
print(f"Cropping ratio  : {C:.3f}       (1.0 = no crop)")
print(f"Distortion D    : {D:.3f}       (lower is better)")
