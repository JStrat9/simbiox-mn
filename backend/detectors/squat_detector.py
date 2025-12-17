# detectors/squat_detector.py

import numpy as np
from utils.geometry import angle_from_arrays
from utils.pose_transform import as_point_tuple
from utils.geometry import angle_with_vertical
from detectors.keypoints_movenet import (
    choose_side,
    extract_side_keypoints,
)
from config import (
    KNEE_MIN_ANGLE, 
    KNEE_MAX_ANGLE,
    PERFECT_DEPTH_MIN,
    PERFECT_DEPTH_MAX,
    LEAN_THRESHOLD,
    KNEE_FORWARD_THRESHOLD,
    ERROR_REPEAT_THRESHOLD,
)


class SquatDetector:
    def __init__(self):
        self.state = "up"
        self.reps = 0
        self.reached_depth = False
        self.first_squat_done = False
        # self.initial_errors = []
        self.current_rep_errors = {}
        self.squat_errors_sent = set()
        self.last_valid_knee_angle = 90
        self.aborted_descend = False
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
        hip_angle = angle_from_arrays(shoulder, hip, knee)
        # back_angle = angle_from_arrays(shoulder, hip, knee)
        ankle_angle = angle_with_vertical(knee, ankle)

        # Knee angle sanity check
        if 20 < knee_angle < 200:
            self.last_valid_knee_angle = knee_angle
        else:
            knee_angle = self.last_valid_knee_angle

        # -----------------------
        # Zones
        # -----------------------

        in_up_zone = knee_angle > KNEE_MAX_ANGLE
        in_mid_zone = PERFECT_DEPTH_MAX < knee_angle <= KNEE_MAX_ANGLE
        in_depth_zone = PERFECT_DEPTH_MIN <= knee_angle <= PERFECT_DEPTH_MAX
        in_too_deep_zone = knee_angle < PERFECT_DEPTH_MIN

        # -----------------------
        # Errors initialization
        # -----------------------
        current_errors  = []

        rep_feedback = []


        # -----------------------
        # State machine
        # -----------------------
        if self.state == "up" and in_mid_zone:
            self.state = "descending"
            self.aborted_descend = True
        elif self.state == "descending":
            if in_depth_zone:
                self.state = "down"
                self.reps += 1
                self.reached_depth = True
                self.aborted_descend = False
            elif in_up_zone:
                self.state = "up"
                # Aborted descent
                if self.aborted_descend:
                    current_errors.append("No bajas lo suficiente")
                self.aborted_descend = False
        elif self.state == "down" and in_mid_zone:
            self.state = "ascending"
        elif self.state == "ascending" and in_up_zone:
            self.state = "up"
            # Reset errors for next rep
            rep_feedback = [
            err for err, frames in self.current_rep_errors.items()
            if frames >= ERROR_REPEAT_THRESHOLD
            ]
        self.current_rep_errors.clear()
        

        if in_too_deep_zone:
            current_errors .append("Baja demasiado")

        if in_mid_zone or in_depth_zone:
            if hip_angle < LEAN_THRESHOLD:
                current_errors.append("Espalda encorvada")
            if ankle_angle > KNEE_FORWARD_THRESHOLD:
                current_errors.append("Rodillas adelantadas")

        if self.state in ("descending", "down", "ascending"):
            for err in current_errors:
                self.current_rep_errors[err] = (
                    self.current_rep_errors.get(err, 0) +1
                )


        # Filter repeated errors
        feedback_to_send = []

        if self.first_squat_done:
            for err in rep_feedback:
                if err not in self.squat_errors_sent:
                    feedback_to_send.append(err)
                    self.squat_errors_sent.add(err)
        
        
        feedback_to_send = " | ".join(feedback_to_send) if feedback_to_send else ""

        if self.state == "up" and self.reached_depth:
            self.first_squat_done = True
            self.reached_depth = False

        return {
            "valid": True,
            "side": side,
            "state": self.state,
            "reps": self.reps,
            "angles": {
                "knee": knee_angle,
                "hip": hip_angle,
                # "back": back_angle,
                "ankle": ankle_angle,
            },
            "errors": current_errors,
            "feedback": feedback_to_send
        }


