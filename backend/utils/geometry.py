# utils/geometry.py

import numpy as np

EPS = 1e-6

def calculate_angle(a, b, c):
    """
    Calculate angle between three points.
    a, b, c are objects with .x, .y attributes
    """
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])

    return angle_from_arrays(a, b, c)

def angle_from_arrays(a, b, c):
    """Similar as calculate_angle but bu reseives tuples/lists/arrays (xj, y). Useful for genaral processing outside of MediaPipe/MoveNet context."""

    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + EPS)
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))