from math import atan2, cos, sin

import cv2
import numpy as np


class OnlineStabilizer:
    """
    Lightweight per-frame stabilizer callable:
      - estimates prev->curr affine (translation + rotation, no scale)
      - accumulates camera motion (dx, dy, da)
      - smooths the camera path with EMA (alpha in [0,1], higher = smoother)
      - applies the *difference* (smoothed - raw) to current frame

    Usage:
        stab = OnlineStabilizer(alpha=0.90)
        stabilized = stab(frame)   # call per frame

    Notes:
      - Stateless input, stateful instance (keeps prev frame + smoothed path)
      - Border handling: black fill; keep full FOV (no crop)
    """

    def __init__(self, alpha: float = 0.90, ransac_thresh: float = 3.0):
        self.alpha = float(np.clip(alpha, 0.0, 1.0))
        self.ransac_thresh = ransac_thresh
        self.prev_gray = None
        self.accum = np.zeros(3, dtype=np.float32)  # [dx, dy, da]
        self.smooth_accum = np.zeros(3, dtype=np.float32)  # EMA of the path
        self._last_output = None

    def reset(self):
        self.prev_gray = None
        self.accum[:] = 0
        self.smooth_accum[:] = 0
        self._last_output = None

    def __call__(self, frame_bgr: np.ndarray) -> np.ndarray:
        h, w = frame_bgr.shape[:2]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # First frame: just initialize state
        if self.prev_gray is None:
            self.prev_gray = gray
            self._last_output = frame_bgr
            return frame_bgr

        # KLT feature tracking
        pts_prev = cv2.goodFeaturesToTrack(
            self.prev_gray, maxCorners=500, qualityLevel=0.01, minDistance=8
        )
        if pts_prev is None or len(pts_prev) < 6:
            # Not enough features; return last output to avoid jump
            self.prev_gray = gray
            return self._last_output if self._last_output is not None else frame_bgr

        pts_curr, st, err = cv2.calcOpticalFlowPyrLK(
            self.prev_gray, gray, pts_prev, None
        )
        if pts_curr is None:
            self.prev_gray = gray
            return self._last_output if self._last_output is not None else frame_bgr

        good_prev = pts_prev[st.flatten() == 1]
        good_curr = pts_curr[st.flatten() == 1]
        if len(good_curr) < 6:
            self.prev_gray = gray
            return self._last_output if self._last_output is not None else frame_bgr

        # Rigid affine (rotation + translation; scale ~1)
        M, inliers = cv2.estimateAffinePartial2D(
            good_prev,
            good_curr,
            method=cv2.RANSAC,
            ransacReprojThreshold=self.ransac_thresh,
        )
        if M is None:
            self.prev_gray = gray
            return self._last_output if self._last_output is not None else frame_bgr

        # Decompose to dx, dy, da
        dx = float(M[0, 2])
        dy = float(M[1, 2])
        da = float(atan2(M[1, 0], M[0, 0]))  # rotation angle

        # Accumulate camera path and compute smoothed path (EMA)
        self.accum += np.array([dx, dy, da], dtype=np.float32)
        self.smooth_accum = (
            1.0 - self.alpha
        ) * self.smooth_accum + self.alpha * self.accum

        # The transform we need to *apply* is the difference between smoothed and raw
        diff = self.smooth_accum - self.accum
        cx, cy = cos(diff[2]), sin(diff[2])
        # Build 2x3 affine to compensate
        M_comp = np.array([[cx, -cy, diff[0]], [cy, cx, diff[1]]], dtype=np.float32)

        stabilized = cv2.warpAffine(
            frame_bgr,
            M_comp,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )

        self.prev_gray = gray
        self._last_output = stabilized
        return stabilized


def write_stabilized_video(
    in_path: str,
    out_path: str,
    stabilizer: OnlineStabilizer,
    fourcc: str = "mp4v",
    fps: float | None = None,
    limit_frames: int | None = None,
):
    """
    Minimal writer: reads `in_path`, applies `stabilizer(frame)` per frame, writes to `out_path`.
    """
    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {in_path}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps is None:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*fourcc), fps, (w, h))
    if not vw.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open VideoWriter: {out_path}")

    stabilizer.reset()
    n = 0
    while True:
        if limit_frames is not None and n >= limit_frames:
            break
        ok, frame = cap.read()
        if not ok:
            break
        out = stabilizer(frame)
        vw.write(out)
        n += 1

    vw.release()
    cap.release()
