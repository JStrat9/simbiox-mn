# detectors/squat_detector.py

import numpy as np
from utils.geometry import angle_from_arrays
from utils.pose_transform import as_point_tuple
from detectors.keypoints_movenet import (
    choose_side,
    extract_side_keypoints,
)
from config import KNEE_MIN_ANGLE, KNEE_MAX_ANGLE


class SquatDetector:
    def __init__(self):
        self.state = "up"
        self.rep_count = 0

    def analyze(self, person_kp: np.ndarray):
        """
        Análisis de una sola persona detectada por MoveNet MultiPose.
        person_kp = array (17, 3) con [y, x, score] * 17 keypoints.
        """

        if person_kp is None or person_kp.shape != (17, 3):
            return {"valid": False, "error": "invalid_keypoints"}

        # Choose left or right side
        side = choose_side(person_kp)

        # Extract keypoints for that side
        kp = extract_side_keypoints(person_kp, side)

        shoulder = as_point_tuple(kp["shoulder"])
        hip      = as_point_tuple(kp["hip"])
        knee     = as_point_tuple(kp["knee"])
        ankle    = as_point_tuple(kp["ankle"])

        # Compute angles
        knee_angle = angle_from_arrays(hip, knee, ankle)
        back_angle = angle_from_arrays(shoulder, hip, knee)

        # Error detection
        errors = []

        if knee_angle < KNEE_MIN_ANGLE:
            errors.append("too_low")
        if knee_angle > KNEE_MAX_ANGLE:
            errors.append("not_low_enough")

        # State machine for reps
        if self.state == "up":
            if knee_angle < 140:       # Descending
                self.state = "down"

        elif self.state == "down":
            if knee_angle > 165:       # Back up
                self.state = "up"
                self.rep_count += 1

        return {
            "valid": True,
            "side": side,
            "angles": {
                "knee": knee_angle,
                "back": back_angle,
            },
            "state": self.state,
            "reps": self.rep_count,
            "errors": errors,
        }
