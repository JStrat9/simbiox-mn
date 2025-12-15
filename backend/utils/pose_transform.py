# utils/pose_transform.py
import numpy as np

def to_pixel(x: float, y: float, frame_width: int, frame_height: int):
    """
    Convierte coordenadas normalizadas (0–1) a píxeles.
    """
    return int(x * frame_width), int(y * frame_height)

def as_point_tuple(kp):
    """
    kp: np.array([x, y, score])
    Devuelve (x, y)
    """
    return float(kp[0]), float(kp[1])
