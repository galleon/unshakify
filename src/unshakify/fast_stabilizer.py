import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
import math


class FastStabilizer:
    """
    Fast-Stab inspired video stabilizer with optical flow and confidence mapping.

    This implementation is inspired by the Fast-Stab paper but simplified for real-time
    processing and compatibility with Mac M3 (Apple Silicon). It uses:
    - Dense optical flow estimation
    - Confidence map generation
    - Homography-based transformation
    - Temporal smoothing with adaptive parameters

    Key improvements over basic stabilization:
    - Better motion estimation through dense flow
    - Confidence-based feature filtering
    - Adaptive smoothing based on motion confidence
    - Homography transformations for better perspective handling
    """

    def __init__(
        self,
        alpha: float = 0.9,
        flow_method: str = "farneback",
        confidence_threshold: float = 0.6,
        min_flow_points: int = 1000,
        homography_method: int = cv2.RANSAC,
        ransac_threshold: float = 5.0,
        max_corners: int = 1000,
        quality_level: float = 0.01,
        min_distance: float = 10,
    ):
        """
        Initialize the Fast-Stab inspired stabilizer.

        Args:
            alpha: Temporal smoothing factor (0-1, higher = smoother)
            flow_method: Optical flow method ("farneback" or "lucas_kanade")
            confidence_threshold: Minimum confidence for flow points (0-1)
            min_flow_points: Minimum number of confident flow points needed
            homography_method: Method for homography estimation
            ransac_threshold: RANSAC threshold for homography estimation
            max_corners: Maximum corners for Lucas-Kanade method
            quality_level: Quality level for corner detection
            min_distance: Minimum distance between corners
        """
        self.alpha = np.clip(alpha, 0.0, 1.0)
        self.flow_method = flow_method
        self.confidence_threshold = confidence_threshold
        self.min_flow_points = min_flow_points
        self.homography_method = homography_method
        self.ransac_threshold = ransac_threshold
        self.max_corners = max_corners
        self.quality_level = quality_level
        self.min_distance = min_distance

        # State variables
        self.prev_gray = None
        self.prev_corners = None
        self.cumulative_transform = np.eye(3, dtype=np.float32)
        self.smoothed_transform = np.eye(3, dtype=np.float32)
        self.transform_history = []
        self.confidence_history = []
        self._last_output = None

        # Optical flow parameters
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )

        self.farneback_params = dict(
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )

    def reset(self):
        """Reset the stabilizer state."""
        self.prev_gray = None
        self.prev_corners = None
        self.cumulative_transform = np.eye(3, dtype=np.float32)
        self.smoothed_transform = np.eye(3, dtype=np.float32)
        self.transform_history = []
        self.confidence_history = []
        self._last_output = None

    def _compute_dense_flow(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        """Compute dense optical flow using Farneback method."""
        try:
            flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, **self.farneback_params)
            return flow
        except cv2.error:
            return None

    def _compute_sparse_flow(
        self, prev_gray: np.ndarray, curr_gray: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute sparse optical flow using Lucas-Kanade method."""
        # Detect corners in previous frame
        if self.prev_corners is None:
            corners = cv2.goodFeaturesToTrack(
                prev_gray,
                maxCorners=self.max_corners,
                qualityLevel=self.quality_level,
                minDistance=self.min_distance
            )
            self.prev_corners = corners

        if self.prev_corners is None or len(self.prev_corners) < 10:
            return None, None, None

        # Calculate optical flow
        next_corners, status, error = cv2.calcOpticalFlowPyrLK(
            prev_gray, curr_gray, self.prev_corners, None, **self.lk_params
        )

        # Filter good points
        good_old = self.prev_corners[status == 1]
        good_new = next_corners[status == 1]

        # Update corners for next iteration
        self.prev_corners = next_corners

        return good_old, good_new, error[status == 1]

    def _generate_confidence_map(
        self, prev_gray: np.ndarray, curr_gray: np.ndarray, flow: np.ndarray
    ) -> np.ndarray:
        """
        Generate confidence map for optical flow.

        This is a simplified version of confidence estimation inspired by Fast-Stab.
        It considers flow magnitude, gradient consistency, and temporal coherence.
        """
        h, w = prev_gray.shape
        confidence = np.ones((h, w), dtype=np.float32)

        if flow is None:
            return confidence * 0.1  # Low confidence if no flow

        # Flow magnitude confidence (prefer moderate motion)
        if len(flow.shape) == 3 and flow.shape[2] == 2:
            flow_mag = np.sqrt(flow[:, :, 0]**2 + flow[:, :, 1]**2)
            mag_conf = np.exp(-flow_mag / 10.0)  # Penalize very large motions
            confidence *= mag_conf

        # Gradient consistency confidence
        grad_x_prev = cv2.Sobel(prev_gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y_prev = cv2.Sobel(prev_gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_x_curr = cv2.Sobel(curr_gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y_curr = cv2.Sobel(curr_gray, cv2.CV_64F, 0, 1, ksize=3)

        grad_mag_prev = np.sqrt(grad_x_prev**2 + grad_y_prev**2)
        grad_mag_curr = np.sqrt(grad_x_curr**2 + grad_y_curr**2)

        # Areas with strong gradients are more reliable
        grad_conf = (grad_mag_prev + grad_mag_curr) / (2 * 255.0)
        grad_conf = np.clip(grad_conf, 0.1, 1.0)
        confidence *= grad_conf

        return confidence

    def _estimate_homography_from_flow(
        self, good_old: np.ndarray, good_new: np.ndarray, confidence_weights: np.ndarray
    ) -> Optional[np.ndarray]:
        """Estimate homography transformation from point correspondences."""
        if len(good_old) < 4:
            return None

        try:
            # Use confidence weights if available
            if confidence_weights is not None and len(confidence_weights) == len(good_old):
                # Filter points by confidence
                conf_mask = confidence_weights > self.confidence_threshold
                if np.sum(conf_mask) < 4:
                    conf_mask = confidence_weights > (self.confidence_threshold * 0.5)

                if np.sum(conf_mask) >= 4:
                    good_old = good_old[conf_mask]
                    good_new = good_new[conf_mask]

            # Estimate homography with RANSAC
            H, mask = cv2.findHomography(
                good_old, good_new,
                method=self.homography_method,
                ransacReprojThreshold=self.ransac_threshold,
                confidence=0.99
            )

            return H if H is not None else np.eye(3, dtype=np.float32)

        except cv2.error:
            return np.eye(3, dtype=np.float32)

    def _decompose_homography(self, H: np.ndarray) -> Dict[str, float]:
        """Decompose homography into rotation, scale, and translation components."""
        if H is None:
            return {"rotation": 0, "scale_x": 1, "scale_y": 1, "tx": 0, "ty": 0}

        try:
            # Extract rotation and scale
            rotation = math.atan2(H[1, 0], H[0, 0])
            scale_x = math.sqrt(H[0, 0]**2 + H[1, 0]**2)
            scale_y = math.sqrt(H[0, 1]**2 + H[1, 1]**2)

            # Ensure reasonable values
            rotation = np.clip(rotation, -np.pi/4, np.pi/4)  # Limit rotation
            scale_x = np.clip(scale_x, 0.8, 1.2)  # Limit scaling
            scale_y = np.clip(scale_y, 0.8, 1.2)

            return {
                "rotation": rotation,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "tx": H[0, 2],
                "ty": H[1, 2]
            }
        except:
            return {"rotation": 0, "scale_x": 1, "scale_y": 1, "tx": 0, "ty": 0}

    def _adaptive_smoothing(self, current_transform: np.ndarray, confidence: float) -> np.ndarray:
        """Apply adaptive temporal smoothing based on motion confidence."""
        # Adapt smoothing factor based on confidence
        adaptive_alpha = self.alpha * confidence
        adaptive_alpha = np.clip(adaptive_alpha, 0.1, 0.95)

        # EMA smoothing
        if len(self.transform_history) == 0:
            smoothed = current_transform.copy()
        else:
            prev_smoothed = self.transform_history[-1]
            smoothed = (1 - adaptive_alpha) * prev_smoothed + adaptive_alpha * current_transform

        return smoothed

    def __call__(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Process a single frame and return stabilized result."""
        h, w = frame_bgr.shape[:2]
        curr_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # Initialize on first frame
        if self.prev_gray is None:
            self.prev_gray = curr_gray
            self._last_output = frame_bgr
            return frame_bgr

        # Compute optical flow based on selected method
        if self.flow_method == "farneback":
            try:
                # Use Farneback dense optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    self.prev_gray,
                    curr_gray,
                    None,
                    **self.farneback_params
                )

                # Sample points from dense flow for homography estimation
                y_coords, x_coords = np.mgrid[0:h:20, 0:w:20]
                good_old = np.column_stack([x_coords.ravel(), y_coords.ravel()]).astype(np.float32)

                if flow is not None and len(flow.shape) == 3:
                    flow_sampled = flow[::20, ::20]
                    good_new = good_old + flow_sampled.reshape(-1, 2)
                else:
                    good_new = good_old

                # Generate confidence weights
                confidence_map = self._generate_confidence_map(self.prev_gray, curr_gray, flow)
                conf_sampled = confidence_map[::20, ::20].ravel()

            except cv2.error:
                # Fallback to previous output
                self.prev_gray = curr_gray
                return self._last_output if self._last_output is not None else frame_bgr

        else:  # lucas_kanade
            good_old, good_new, errors = self._compute_sparse_flow(self.prev_gray, curr_gray)

            if good_old is None or len(good_old) < self.min_flow_points:
                self.prev_gray = curr_gray
                return self._last_output if self._last_output is not None else frame_bgr

            # Use inverse of errors as confidence
            conf_sampled = 1.0 / (1.0 + errors)

        # Estimate homography transformation
        H = self._estimate_homography_from_flow(good_old, good_new, conf_sampled)

        if H is None:
            self.prev_gray = curr_gray
            return self._last_output if self._last_output is not None else frame_bgr

        # Update cumulative transform
        self.cumulative_transform = H @ self.cumulative_transform

        # Calculate average confidence
        avg_confidence = np.mean(conf_sampled) if conf_sampled is not None else 0.5
        avg_confidence = np.clip(avg_confidence, 0.1, 1.0)

        # Apply adaptive smoothing
        smoothed_transform = self._adaptive_smoothing(self.cumulative_transform, avg_confidence)

        # Calculate compensation transform
        compensation_transform = smoothed_transform @ np.linalg.inv(self.cumulative_transform)

        # Apply transformation
        try:
            stabilized = cv2.warpPerspective(
                frame_bgr,
                compensation_transform,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0)
            )
        except cv2.error:
            stabilized = frame_bgr

        # Update history
        self.transform_history.append(smoothed_transform)
        self.confidence_history.append(avg_confidence)

        # Keep history bounded
        if len(self.transform_history) > 30:
            self.transform_history.pop(0)
            self.confidence_history.pop(0)

        # Update state
        self.prev_gray = curr_gray
        self._last_output = stabilized

        return stabilized

    def get_stabilization_info(self) -> Dict[str, Any]:
        """Get information about the current stabilization state."""
        if len(self.confidence_history) == 0:
            return {"avg_confidence": 0.0, "transform_norm": 0.0}

        recent_conf = self.confidence_history[-5:] if len(self.confidence_history) >= 5 else self.confidence_history
        avg_confidence = np.mean(recent_conf)

        # Calculate transform magnitude
        if len(self.transform_history) > 0:
            current_transform = self.transform_history[-1]
            transform_norm = np.linalg.norm(current_transform - np.eye(3))
        else:
            transform_norm = 0.0

        return {
            "avg_confidence": float(avg_confidence),
            "transform_norm": float(transform_norm),
            "num_transforms": len(self.transform_history)
        }


def write_fast_stabilized_video(
    in_path: str,
    out_path: str,
    stabilizer: FastStabilizer,
    fourcc: str = "mp4v",
    fps: Optional[float] = None,
    limit_frames: Optional[int] = None,
):
    """
    Process video with Fast-Stab inspired stabilizer.

    Args:
        in_path: Input video path
        out_path: Output video path
        stabilizer: FastStabilizer instance
        fourcc: Video codec fourcc
        fps: Output framerate (uses input fps if None)
        limit_frames: Limit number of frames to process
    """
    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {in_path}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps is None:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Create video writer
    fourcc_code = cv2.VideoWriter_fourcc(*fourcc)
    vw = cv2.VideoWriter(out_path, fourcc_code, fps, (w, h))
    if not vw.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open VideoWriter: {out_path}")

    # Reset stabilizer state
    stabilizer.reset()

    frame_count = 0
    while True:
        if limit_frames is not None and frame_count >= limit_frames:
            break

        ret, frame = cap.read()
        if not ret:
            break

        # Apply stabilization
        stabilized_frame = stabilizer(frame)
        vw.write(stabilized_frame)

        frame_count += 1

        # Print progress every 100 frames
        if frame_count % 100 == 0:
            info = stabilizer.get_stabilization_info()
            print(f"Frame {frame_count}: confidence={info['avg_confidence']:.3f}")

    # Cleanup
    vw.release()
    cap.release()

    print(f"Fast stabilization complete: {frame_count} frames processed")
    final_info = stabilizer.get_stabilization_info()
    print(f"Final stats - Avg confidence: {final_info['avg_confidence']:.3f}")
