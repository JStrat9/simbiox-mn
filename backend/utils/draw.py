# utils/drawing.py

import cv2
import numpy as np

# Pares de keypoints que forman las “articulaciones” a unir
KEYPOINT_EDGES = {
    (0,1), (0,2), (1,3), (2,4),
    (0,5), (0,6), (5,7), (7,9),
    (6,8), (8,10), (5,6), (5,11),
    (6,12), (11,12), (11,13), (13,15),
    (12,14), (14,16)
}

def draw_keypoints(frame: np.ndarray, keypoints: np.ndarray, color=(0,255,0), threshold=0.3):
    """
    Dibuja círculos en los keypoints con score > threshold.
    """
    h, w, _ = frame.shape
    for y, x, c in keypoints:
        if c > threshold:
            cv2.circle(frame, (int(x*w), int(y*h)), 4, color, -1)

def draw_edges(frame: np.ndarray, keypoints: np.ndarray, color=(255,255,255), threshold=0.3):
    """
    Dibuja líneas entre pares de keypoints definidos en KEYPOINT_EDGES.
    """
    h, w, _ = frame.shape
    for i, j in KEYPOINT_EDGES:
        y1, x1, c1 = keypoints[i]
        y2, x2, c2 = keypoints[j]
        if c1 > threshold and c2 > threshold:
            cv2.line(frame, (int(x1*w), int(y1*h)), (int(x2*w), int(y2*h)), color, 2)

def draw_angles(frame: np.ndarray, keypoints: np.ndarray, angles: dict, side: str, color=(0, 255, 255), font_scale=0.5, thickness=2):
    """
    Draws angle values near the corresponding key points.
    Supports squat angles (knee, hip, ankle) and renegade_row angles (elbow, hip_body).
    """

    h, w, _ = frame.shape

    # Keypoint indices based on side
    if side == "left":
        shoulder_idx = 5   # left_shoulder
        elbow_idx    = 7   # left_elbow
        hip_idx      = 11  # left_hip
        knee_idx     = 13  # left_knee
        ankle_idx    = 15  # left_ankle
    else:
        shoulder_idx = 6   # right_shoulder
        elbow_idx    = 8   # right_elbow
        hip_idx      = 12  # right_hip
        knee_idx     = 14  # right_knee
        ankle_idx    = 16  # right_ankle

    def _put(idx: int, label: str, value: float):
        if idx >= len(keypoints):
            return
        y, x, c = keypoints[idx]
        if c > 0.3:
            cv2.putText(frame, f"{label}: {value:.1f}", (int(x * w) + 10, int(y * h) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    # Squat angles
    if 'knee' in angles:
        _put(knee_idx, "Knee", angles['knee'])
    if 'hip' in angles:
        _put(hip_idx, "Hip", angles['hip'])
    if 'ankle' in angles:
        _put(ankle_idx, "Ankle", angles['ankle'])

    # Renegade row angles
    if 'elbow' in angles:
        _put(elbow_idx, "Elbow", angles['elbow'])
    if 'hip_body' in angles:
        _put(hip_idx, "Body", angles['hip_body'])