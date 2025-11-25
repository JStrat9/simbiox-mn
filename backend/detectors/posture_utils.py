from utils.geometry import angle
from detectors.keypoints_movenet import KEYPOINT

def get_point(kp, name):
    """Devuelve ((x, y), confidence) desde el diccionario de keypoints."""
    idx = KEYPOINT[name]
    x, y, c = kp[idx]
    return (x, y), c

def knee_angle_left(kp):
    hip, c1 = get_point(kp, "left_hip")
    knee, c2 = get_point(kp, "left_knee")
    ankle, c3 = get_point(kp, "left_ankle")

    if min(c1, c2, c3) < 0.3:
        return None

    return angle(hip, knee, ankle)

def knee_angle_right(kp):
    hip, c1 = get_point(kp, "right_hip")
    knee, c2 = get_point(kp, "right_knee")
    ankle, c3 = get_point(kp, "right_ankle")

    if min(c1, c2, c3) < 0.3:
        return None

    return angle(hip, knee, ankle)

