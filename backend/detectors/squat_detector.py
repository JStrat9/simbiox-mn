# detectors/squat_detector.py


import numpy as np
from utils.geometry import angle_from_arrays
from utils.pose_transform import as_point_tuple
from utils.geometry import angle_with_vertical
from detectors.keypoints_movenet import (
    choose_side,
    extract_side_keypoints,
    required_keypoints_confident,
)
from config import (
    KNEE_MAX_ANGLE,
    PERFECT_DEPTH_MIN,
    PERFECT_DEPTH_MAX,
    LEAN_THRESHOLD,
    KNEE_FORWARD_THRESHOLD,
    ERROR_REPEAT_THRESHOLD,
    ERROR_REP_COUNT_THRESHOLD,
    KEYPOINT_CONFIDENCE_THRESHOLD,
)
from domain.errors.error_catalog import (
    default_message_key_for_code,
    default_severity_for_code,
)


_CODE_TO_DISPLAY: dict[str, str] = {
    "DEPTH_INSUFFICIENT": "No bajas lo suficiente",
    "DEPTH_EXCESSIVE":    "Baja demasiado",
    "BACK_ROUNDED":       "Espalda encorvada",
    "KNEE_FORWARD":       "Rodillas adelantadas",
}


def _make_error(code: str, **metadata_fields) -> dict:
    return {
        "code": code,
        "message_key": default_message_key_for_code(code),
        "severity": default_severity_for_code(code),
        "metadata": {k: round(v, 2) if isinstance(v, float) else v for k, v in metadata_fields.items()},
    }


class SquatDetector:
    def __init__(self):
        self.state = "up"
        self.reps = 0
        self.reached_depth = False
        self.first_squat_done = False
        self.current_rep_errors = {}
        self.current_rep_error_dicts: dict[str, dict] = {}
        self.error_rep_count: dict[str, int] = {}
        self.confirmed_error_dicts: dict[str, dict] = {}
        self.squat_errors_sent = set()
        self.last_valid_knee_angle = 90
        self.aborted_descend = False
        print("[DETECTOR] SquatDetector created", id(self))

    def clear_reviewed_errors(self):
        confirmed_codes = list(self.confirmed_error_dicts.keys())
        if not confirmed_codes:
            return

        for code in confirmed_codes:
            self.error_rep_count.pop(code, None)
            self.current_rep_errors.pop(code, None)
            self.current_rep_error_dicts.pop(code, None)
            self.squat_errors_sent.discard(code)

        self.confirmed_error_dicts.clear()

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

        if not required_keypoints_confident(kp, ["shoulder", "hip", "knee", "ankle"], KEYPOINT_CONFIDENCE_THRESHOLD):
            confirmed_errors_v2 = [
                self.confirmed_error_dicts[code]
                for code in sorted(self.confirmed_error_dicts.keys())
            ]
            return {
                "valid": True,
                "side": side,
                "state": self.state,
                "reps": self.reps,
                "angles": {},
                "errors": [e["code"] for e in confirmed_errors_v2],
                "errors_v2": confirmed_errors_v2,
                "feedback": "",
            }

        shoulder = as_point_tuple(kp["shoulder"])
        hip      = as_point_tuple(kp["hip"])
        knee     = as_point_tuple(kp["knee"])
        ankle    = as_point_tuple(kp["ankle"])

        # -----------------------
        # Angles
        # -----------------------

        knee_angle = angle_from_arrays(hip, knee, ankle)
        hip_angle = angle_from_arrays(shoulder, hip, knee)
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
        current_errors_v2: list[dict] = []

        rep_feedback: list[str] = []


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
                if self.aborted_descend:
                    err = _make_error("DEPTH_INSUFFICIENT", knee_angle=knee_angle)
                    current_errors_v2.append(err)
                    self.error_rep_count["DEPTH_INSUFFICIENT"] = (
                        self.error_rep_count.get("DEPTH_INSUFFICIENT", 0) + 1
                    )
                    if self.error_rep_count["DEPTH_INSUFFICIENT"] == ERROR_REP_COUNT_THRESHOLD:
                        self.confirmed_error_dicts["DEPTH_INSUFFICIENT"] = err
                self.aborted_descend = False
        elif self.state == "down" and in_mid_zone:
            self.state = "ascending"
        elif self.state == "ascending" and in_up_zone:
            self.state = "up"
            rep_feedback = [
                code for code, frames in self.current_rep_errors.items()
                if frames >= ERROR_REPEAT_THRESHOLD
            ]
            for code in rep_feedback:
                self.error_rep_count[code] = self.error_rep_count.get(code, 0) + 1
                if self.error_rep_count[code] == ERROR_REP_COUNT_THRESHOLD:
                    err_dict = self.current_rep_error_dicts.get(code)
                    if err_dict:
                        self.confirmed_error_dicts[code] = err_dict
            self.current_rep_errors.clear()
            self.current_rep_error_dicts.clear()
        

        if in_too_deep_zone:
            current_errors_v2.append(_make_error("DEPTH_EXCESSIVE", knee_angle=knee_angle))

        if in_mid_zone or in_depth_zone:
            if hip_angle < LEAN_THRESHOLD:
                current_errors_v2.append(_make_error("BACK_ROUNDED", hip_angle=hip_angle))
            if ankle_angle > KNEE_FORWARD_THRESHOLD:
                current_errors_v2.append(_make_error("KNEE_FORWARD", ankle_angle=ankle_angle))

        if self.state in ("descending", "down", "ascending"):
            for err in current_errors_v2:
                code = err["code"]
                self.current_rep_errors[code] = (
                    self.current_rep_errors.get(code, 0) + 1
                )
                self.current_rep_error_dicts[code] = err


        # Filter repeated errors
        feedback_to_send = []

        if self.first_squat_done:
            for err in rep_feedback:
                if err not in self.squat_errors_sent:
                    feedback_to_send.append(err)
                    self.squat_errors_sent.add(err)
        
        
        feedback_to_send = " | ".join(
            _CODE_TO_DISPLAY.get(code, code) for code in feedback_to_send
        ) if feedback_to_send else ""

        if self.state == "up" and self.reached_depth:
            self.first_squat_done = True
            self.reached_depth = False

        confirmed_errors_v2 = [
            self.confirmed_error_dicts[code]
            for code in sorted(self.confirmed_error_dicts.keys())
        ]

        return {
            "valid": True,
            "side": side,
            "state": self.state,
            "reps": self.reps,
            "angles": {
                "knee": knee_angle,
                "hip": hip_angle,
                "ankle": ankle_angle,
            },
            "errors": [e["code"] for e in confirmed_errors_v2],
            "errors_v2": confirmed_errors_v2,
            "feedback": feedback_to_send,
        }


