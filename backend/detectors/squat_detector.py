# detectors/squat_detector.py

import numpy as np
from utils.geometry import angle_from_arrays
from utils.pose_transform import as_point_tuple
from detectors.keypoints_movenet import (
    choose_side,
    extract_side_keypoints,
)
from config import (
    KNEE_MIN_ANGLE, 
    KNEE_MAX_ANGLE,
    PERFECT_DEPTH_MIN,
    PERFECT_DEPTH_MAX,
)


class SquatDetector:
    def __init__(self):
        self.state = "up"
        self.reps = 0
        print("🔥 SquatDetector creado", id(self))


    def analyze(self, person_kp: np.ndarray):
        """
        person_kp: np.ndarray (17, 3) -> [y, x, score]
        """

        # -----------------------
        # Basic validations
        # -----------------------

        if person_kp is None or person_kp.shape != (17, 3):
            return {"valid": False}

        # Choose left or right side
        side = choose_side(person_kp)
        # Extract keypoints for that side
        kp = extract_side_keypoints(person_kp, side)

        shoulder = as_point_tuple(kp["shoulder"])
        hip      = as_point_tuple(kp["hip"])
        knee     = as_point_tuple(kp["knee"])
        ankle    = as_point_tuple(kp["ankle"])

        # -----------------------
        # Angles
        # -----------------------

        knee_angle = angle_from_arrays(hip, knee, ankle)
        back_angle = angle_from_arrays(shoulder, hip, knee)

        # -----------------------
        # Zones
        # -----------------------

        in_up_zone = knee_angle > KNEE_MAX_ANGLE
        in_mid_zone = PERFECT_DEPTH_MAX < knee_angle <= KNEE_MAX_ANGLE
        in_depth_zone = PERFECT_DEPTH_MIN <= knee_angle <= PERFECT_DEPTH_MAX
        in_too_deep_zone = knee_angle < PERFECT_DEPTH_MIN

        # -----------------------
        # State machine
        # -----------------------

        if self.state == "up":
            if in_mid_zone:
                self.state = "descending"
        
        elif self.state == "descending":
            if in_depth_zone:
                self.state = "down"
                self.reps += 1
            elif in_up_zone:
                self.state = "up" # aborted descent

        elif self.state == "down":
            if in_mid_zone:
                self.state = "ascending"
        
        elif self.state == "ascending":
            if in_up_zone:
                self.state = "up"
        
        # -----------------------
        # Errors
        # -----------------------

        errors = []

        if in_too_deep_zone:
            errors.append("too_low")
        elif in_mid_zone:
            errors.append("not_low_enough")

        return {
            "valid": True,
            "side": side,
            "state": self.state,
            "reps": self.reps,
            "angles": {
                "knee": knee_angle,
                "back": back_angle,
            },
            "errors": errors,
        }


