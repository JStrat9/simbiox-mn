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

def angle_with_vertical(p1, p2):
    """ 
    Calculate angle between the line defined by points p1 and p2 and the vertical axis.
    Useful for measuring lean angles, e.g, back or torso lean and tibia lean for knee tracking.

    p1, p2 tuples / arrays (x, y)
    returns angle in degrees (0º = perfectly vertical)
    """

    p1 = np.array(p1)
    p2 = np.array(p2)

    v = p2 - p1
    v_norm = np.linalg.norm(v)
    if v_norm < EPS:
        return 0.0
    
    v = v/v_norm

    vertical = np.array([0.0, - 1.0]) # Vector vertical unitario hacia arriba (y-axis up)
    cos_angle = np.clip(np.dot(v, vertical), -1.0, 1.0)

    return np.degrees(np.arccos(cos_angle))