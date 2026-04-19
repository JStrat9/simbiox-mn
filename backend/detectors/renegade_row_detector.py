# detectors/renegade_row_detector.py

import numpy as np
from utils.geometry import angle_from_arrays
from utils.pose_transform import as_point_tuple
from detectors.keypoints_movenet import (
    choose_side,
    extract_upper_body_keypoints,
)
from config import (
    RENEGADE_ROW_UP_ANGLE,
    RENEGADE_ROW_DOWN_ANGLE,
    RENEGADE_ROW_HIP_SAG_THRESHOLD,
    ERROR_REPEAT_THRESHOLD,
)
from domain.errors.error_catalog import (
    default_message_key_for_code,
    default_severity_for_code,
)


_CODE_TO_DISPLAY: dict[str, str] = {
    "RANGE_INSUFFICIENT": "No completas el tirón",
    "HIP_SAGGING":        "Cadera hundida",
}


def _make_error(code: str, **metadata_fields) -> dict:
    return {
        "code": code,
        "message_key": default_message_key_for_code(code),
        "severity": default_severity_for_code(code),
        "metadata": {k: round(v, 2) if isinstance(v, float) else v for k, v in metadata_fields.items()},
    }


class RenegadeRowDetector:
    def __init__(self):
        # Estados según posición física del brazo:
        #   "down"     → brazo abajo, extendido en plancha (ángulo codo alto, ~180°)
        #   "pulling"  → brazo subiendo, codo flexionándose
        #   "up"       → brazo arriba, tirón completo (ángulo codo bajo, <90°)
        #   "lowering" → brazo bajando de vuelta a plancha
        self.state = "down"
        self.reps = 0
        self.completed_pull = False
        self.first_rep_done = False
        self.current_rep_errors = {}
        self.renegade_row_errors_sent = set()
        self.last_valid_elbow_angle = 150
        self.aborted_pull = False
        self.locked_side: str | None = None
        print("[DETECTOR] RenegadeRowDetector created", id(self))

    def analyze(self, person_kp: np.ndarray):
        """
        person_kp: np.ndarray (17, 3) -> [y, x, score]
        """
        if person_kp is None or person_kp.shape != (17, 3):
            return {"valid": False}

        if self.state == "down":
            new_side = choose_side(person_kp)
            if new_side != self.locked_side:
                self.locked_side = new_side
                self.last_valid_elbow_angle = 150
        side = self.locked_side or choose_side(person_kp)
        kp = extract_upper_body_keypoints(person_kp, side)

        shoulder = as_point_tuple(kp["shoulder"])
        elbow    = as_point_tuple(kp["elbow"])
        wrist    = as_point_tuple(kp["wrist"])
        hip      = as_point_tuple(kp["hip"])
        ankle    = as_point_tuple(kp["ankle"])

        # -----------------------
        # Angles
        # -----------------------

        elbow_angle    = angle_from_arrays(shoulder, elbow, wrist)
        hip_body_angle = angle_from_arrays(shoulder, hip, ankle)

        # Elbow angle sanity check
        if 10 < elbow_angle < 200:
            self.last_valid_elbow_angle = elbow_angle
        else:
            elbow_angle = self.last_valid_elbow_angle

        # -----------------------
        # Zones
        # Ángulo codo ALTO (>140°) = brazo abajo (plancha)
        # Ángulo codo BAJO (<90°)  = brazo arriba (tirón completo)
        # -----------------------

        in_down_zone = elbow_angle > RENEGADE_ROW_UP_ANGLE    # brazo abajo, extendido
        in_mid_zone  = RENEGADE_ROW_DOWN_ANGLE <= elbow_angle <= RENEGADE_ROW_UP_ANGLE
        in_up_zone   = elbow_angle < RENEGADE_ROW_DOWN_ANGLE  # brazo arriba, tirón completo

        # -----------------------
        # Errors initialization
        # -----------------------
        current_errors_v2: list[dict] = []
        rep_feedback: list[str] = []

        # -----------------------
        # State machine
        # -----------------------
        if self.state == "down" and in_mid_zone:
            self.state = "pulling"
            self.aborted_pull = True
        elif self.state == "pulling":
            if in_up_zone:
                self.state = "up"
                self.reps += 1
                self.completed_pull = True
                self.aborted_pull = False
            elif in_down_zone:
                self.state = "down"
                if self.aborted_pull:
                    current_errors_v2.append(_make_error("RANGE_INSUFFICIENT", elbow_angle=elbow_angle))
                self.aborted_pull = False
        elif self.state == "up" and in_mid_zone:
            self.state = "lowering"
        elif self.state == "lowering" and in_down_zone:
            self.state = "down"
            rep_feedback = [
                err for err, frames in self.current_rep_errors.items()
                if frames >= ERROR_REPEAT_THRESHOLD
            ]
            self.current_rep_errors.clear()

        # HIP_SAGGING check during active phases
        if self.state in ("pulling", "up", "lowering"):
            if hip_body_angle < RENEGADE_ROW_HIP_SAG_THRESHOLD:
                current_errors_v2.append(_make_error("HIP_SAGGING", hip_body_angle=hip_body_angle))

        if self.state in ("pulling", "up", "lowering"):
            for err in current_errors_v2:
                code = err["code"]
                self.current_rep_errors[code] = (
                    self.current_rep_errors.get(code, 0) + 1
                )

        # Filter repeated errors
        feedback_to_send = []

        if self.first_rep_done:
            for err in rep_feedback:
                if err not in self.renegade_row_errors_sent:
                    feedback_to_send.append(err)
                    self.renegade_row_errors_sent.add(err)

        feedback_to_send = " | ".join(
            _CODE_TO_DISPLAY.get(code, code) for code in feedback_to_send
        ) if feedback_to_send else ""

        if self.state == "down" and self.completed_pull:
            self.first_rep_done = True
            self.completed_pull = False

        return {
            "valid": True,
            "side": side,
            "state": self.state,
            "reps": self.reps,
            "angles": {
                "elbow": elbow_angle,
                "hip_body": hip_body_angle,
            },
            "errors": [e["code"] for e in current_errors_v2],
            "errors_v2": current_errors_v2,
            "feedback": feedback_to_send,
        }
