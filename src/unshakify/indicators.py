"""
indicators.py — Product indicators for referee-cam video stabilization
Dependencies: opencv-python-headless, numpy

Indicators:
- Processing latency per frame (ms/frame)  -> measure_latency(...)
- Stability score S (smoothness improvement) -> stability_score_from_video(...)
- Cropping ratio C (retained non-black pixels) -> cropping_ratio_from_video(...)
- Distortion value D (fidelity to original; 1 - SSIM) -> distortion_value_from_videos(...)

Usage example (pseudo):
    # 1) Benchmark your stabilizer function on a raw video:
    ms_per_frame = measure_latency(raw_path, my_stabilize_fn)

    # 2) Compute indicators from the raw vs stabilized videos you produced:
    S = stability_score_from_video(raw_path), stability_score_from_video(stab_path)
    C = cropping_ratio_from_video(stab_path)
    D = distortion_value_from_videos(raw_path, stab_path)

    # 3) Report: S_improvement = 1 - (S_after / S_before)  (higher is better)
"""

import time
from typing import Callable

import cv2
import numpy as np

# ---------- Generic video IO ----------


def _open_video(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    return cap


def _read_frame(cap, to_gray: bool = False) -> np.ndarray | None:
    ok, frame = cap.read()
    if not ok:
        return None
    if to_gray:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame


def _video_shape(path: str) -> tuple[int, int]:
    cap = _open_video(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return (h, w)


# ---------- Indicator 1: Processing latency (ms/frame) ----------


def measure_latency(
    raw_video_path: str,
    stabilize_fn: Callable[[np.ndarray], np.ndarray],
    warmup_frames: int = 5,
    max_frames: int | None = None,
) -> float:
    """
    Runs `stabilize_fn(frame)` on each frame and returns average latency (ms/frame).
    Assumes stabilize_fn is pure per-frame (stateless or internally stateful).
    """
    cap = _open_video(raw_video_path)
    n, total_ms = 0, 0.0

    # Warmup
    for _ in range(warmup_frames):
        frame = _read_frame(cap)
        if frame is None:
            break
        _ = stabilize_fn(frame)

    # Timed run
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        if max_frames is not None and n >= max_frames:
            break
        frame = _read_frame(cap)
        if frame is None:
            break
        t0 = time.perf_counter()
        _ = stabilize_fn(frame)
        t1 = time.perf_counter()
        total_ms += (t1 - t0) * 1000.0
        n += 1

    cap.release()
    if n == 0:
        return float("nan")
    return total_ms / n


# ---------- Helper: Estimate per-frame global translation magnitude ----------


def _camera_motion_magnitudes(
    video_path: str, max_frames: int | None = None
) -> np.ndarray:
    """
    Returns an array of per-step translation magnitudes |(dx,dy)| estimated via
    sparse feature tracking + robust affine (rigid) fit.
    """
    cap = _open_video(video_path)
    prev = _read_frame(cap, to_gray=True)
    if prev is None:
        cap.release()
        return np.array([])

    motions = []
    frame_idx = 0
    while True:
        if max_frames is not None and frame_idx >= max_frames:
            break
        frame = _read_frame(cap, to_gray=True)
        if frame is None:
            break

        # Good features
        pts_prev = cv2.goodFeaturesToTrack(
            prev, maxCorners=500, qualityLevel=0.01, minDistance=8
        )
        if pts_prev is not None and len(pts_prev) >= 6:
            pts_next, st, err = cv2.calcOpticalFlowPyrLK(prev, frame, pts_prev, None)
            good_prev = pts_prev[st.flatten() == 1]
            good_next = pts_next[st.flatten() == 1] if pts_next is not None else None

            if good_next is not None and len(good_next) >= 6:
                # Rigid (no scale) approx via estimateAffinePartial2D
                M, inliers = cv2.estimateAffinePartial2D(
                    good_prev, good_next, method=cv2.RANSAC, ransacReprojThreshold=3.0
                )
                if M is not None:
                    dx, dy = float(M[0, 2]), float(M[1, 2])
                    motions.append(np.hypot(dx, dy))

        prev = frame
        frame_idx += 1

    cap.release()
    return np.array(motions, dtype=np.float32)


# ---------- Indicator 2: Stability score ----------


def stability_score_from_video(
    video_path: str, max_frames: int | None = None
) -> float:
    """
    A lower value means smoother video. We return the RMS of per-step translation magnitudes.
    For reporting "improvement", compute:  S_impr = 1 - (S_after / S_before)  (clamped to [0,1]).
    """
    motions = _camera_motion_magnitudes(video_path, max_frames=max_frames)
    if motions.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean(np.square(motions))))


def stability_improvement(
    before_video: str, after_video: str, max_frames: int | None = None
) -> float:
    """
    Convenience: returns improvement in [0, 1] where higher is better.
    """
    s_before = stability_score_from_video(before_video, max_frames=max_frames)
    s_after = stability_score_from_video(after_video, max_frames=max_frames)
    if not np.isfinite(s_before) or not np.isfinite(s_after) or s_before == 0:
        return float("nan")
    return float(np.clip(1.0 - (s_after / s_before), 0.0, 1.0))


# ---------- Indicator 3: Cropping ratio (retained non-black pixels) ----------


def cropping_ratio_from_video(
    video_path: str, threshold: int = 3, max_frames: int | None = None
) -> float:
    """
    Estimates how much of the frame is "valid" (non-black) after stabilization.
    Returns average fraction of non-black pixels per frame (1.0 = no cropping).
    """
    cap = _open_video(video_path)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    full = float(h * w)
    ratios = []
    n = 0

    while True:
        if max_frames is not None and n >= max_frames:
            break
        frame = _read_frame(cap)
        if frame is None:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Non-black mask (tolerant)
        mask = (gray > threshold).astype(np.uint8)
        ratios.append(float(mask.sum()) / full)
        n += 1

    cap.release()
    if len(ratios) == 0:
        return float("nan")
    return float(np.mean(ratios))


# ---------- Indicator 4: Distortion value D via SSIM (1 - SSIM) ----------


def _ssim_gray(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Simple SSIM (grayscale) without skimage; windowless approximation for speed.
    Good enough as a fidelity proxy (higher SSIM = less distortion).
    """
    img1 = img1.astype(np.float32)
    img2 = img2.astype(np.float32)
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = cv2.blur(img1, (7, 7))
    mu2 = cv2.blur(img2, (7, 7))
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.blur(img1 * img1, (7, 7)) - mu1_sq
    sigma2_sq = cv2.blur(img2 * img2, (7, 7)) - mu2_sq
    sigma12 = cv2.blur(img1 * img2, (7, 7)) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2) + 1e-8
    )
    return float(np.clip(ssim_map.mean(), 0.0, 1.0))


def _common_crop(fr1: np.ndarray, fr2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Crops both frames to their shared non-black area to avoid border bias.
    """

    def valid_mask(x):
        g = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
        return (g > 3).astype(np.uint8)

    m1 = valid_mask(fr1)
    m2 = valid_mask(fr2)
    m = cv2.bitwise_and(m1, m2)
    # If mask is empty, fallback to center crop of min dims
    if m.sum() < 100:
        h = min(fr1.shape[0], fr2.shape[0])
        w = min(fr1.shape[1], fr2.shape[1])
        y0 = (fr1.shape[0] - h) // 2
        x0 = (fr1.shape[1] - w) // 2
        a = fr1[y0 : y0 + h, x0 : x0 + w]
        y0 = (fr2.shape[0] - h) // 2
        x0 = (fr2.shape[1] - w) // 2
        b = fr2[y0 : y0 + h, x0 : x0 + w]
        return a, b

    ys, xs = np.where(m > 0)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    return fr1[y0 : y1 + 1, x0 : x1 + 1], fr2[y0 : y1 + 1, x0 : x1 + 1]


def distortion_value_from_videos(
    raw_video_path: str, stabilized_video_path: str, max_frames: int | None = None
) -> float:
    """
    Fidelity proxy: average (1 - SSIM) between raw frame and stabilized frame at the same index,
    after cropping both to their common valid area. 0 = identical, higher = more distortion.
    """
    cap_a = _open_video(raw_video_path)
    cap_b = _open_video(stabilized_video_path)

    n, vals = 0, []
    while True:
        if max_frames is not None and n >= max_frames:
            break
        fa = _read_frame(cap_a)
        fb = _read_frame(cap_b)
        if fa is None or fb is None:
            break
        a, b = _common_crop(fa, fb)
        ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
        gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
        # Resize to match, if off by a few pixels
        if ga.shape != gb.shape:
            h = min(ga.shape[0], gb.shape[0])
            w = min(ga.shape[1], gb.shape[1])
            ga = ga[:h, :w]
            gb = gb[:h, :w]
        ssim = _ssim_gray(ga, gb)
        vals.append(1.0 - ssim)
        n += 1

    cap_a.release()
    cap_b.release()
    if len(vals) == 0:
        return float("nan")
    return float(np.mean(vals))
