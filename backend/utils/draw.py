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
