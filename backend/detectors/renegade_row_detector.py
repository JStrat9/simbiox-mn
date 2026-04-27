# detectors/renegade_row_detector.py

import numpy as np
from utils.geometry import angle_from_arrays
from utils.pose_transform import as_point_tuple
from detectors.keypoints_movenet import (
    choose_side,
    extract_upper_body_keypoints,
    required_keypoints_confident,
)
from config import (
    RENEGADE_ROW_UP_ANGLE,
    RENEGADE_ROW_DOWN_ANGLE,
    RENEGADE_ROW_ELBOW_TOP_MIN,
    RENEGADE_ROW_ELBOW_TOP_MAX,
    RENEGADE_ROW_HIP_SAG_THRESHOLD,
    RENEGADE_ROW_HIP_HIGH_THRESHOLD,
    ERROR_REPEAT_THRESHOLD,
    ERROR_REP_COUNT_THRESHOLD,
    KEYPOINT_CONFIDENCE_THRESHOLD,
)
from domain.errors.error_catalog import (
    default_message_key_for_code,
    default_severity_for_code,
)


_CODE_TO_DISPLAY: dict[str, str] = {
    "RANGE_INSUFFICIENT": "No completas el tirón",
    "ELBOW_OVERFLEXION":  "Flexionas demasiado el codo",
    "HIP_SAGGING":        "Cadera hundida",
    "HIP_HIGH":           "Cadera alta",
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
        #   "up"       → brazo arriba, tirón completo (ángulo codo bajo, <=90°)
        #   "lowering" → brazo bajando de vuelta a plancha
        self.state = "down"
        self.reps = 0
        self.completed_pull = False
        self.first_rep_done = False
        self.current_rep_errors = {}
        self.current_rep_error_dicts: dict[str, dict] = {}
        self.error_rep_count: dict[str, int] = {}
        self.confirmed_error_dicts: dict[str, dict] = {}
        self.renegade_row_errors_sent = set()
        self.last_valid_elbow_angle = 150
        self.aborted_pull = False
        self.locked_side: str | None = None
        self.current_attempt_min_elbow_angle: float | None = None
        print("[DETECTOR] RenegadeRowDetector created", id(self))

    def clear_reviewed_errors(self):
        confirmed_codes = list(self.confirmed_error_dicts.keys())
        self.current_attempt_min_elbow_angle = None
        if not confirmed_codes:
            return

        for code in confirmed_codes:
            self.error_rep_count.pop(code, None)
            self.current_rep_errors.pop(code, None)
            self.current_rep_error_dicts.pop(code, None)
            self.renegade_row_errors_sent.discard(code)

        self.confirmed_error_dicts.clear()

    def _start_pull_attempt(self, elbow_angle: float) -> None:
        self.current_attempt_min_elbow_angle = elbow_angle

    def _track_pull_attempt(self, elbow_angle: float) -> None:
        if self.current_attempt_min_elbow_angle is None:
            self.current_attempt_min_elbow_angle = elbow_angle
            return
        self.current_attempt_min_elbow_angle = min(
            self.current_attempt_min_elbow_angle,
            elbow_angle,
        )

    def _build_elbow_top_error(self) -> dict | None:
        min_angle = self.current_attempt_min_elbow_angle
        self.current_attempt_min_elbow_angle = None
        if min_angle is None:
            return None

        metadata = {
            "elbow_angle": min_angle,
            "target_min": RENEGADE_ROW_ELBOW_TOP_MIN,
            "target_max": RENEGADE_ROW_ELBOW_TOP_MAX,
        }

        if min_angle > RENEGADE_ROW_ELBOW_TOP_MAX:
            return _make_error("RANGE_INSUFFICIENT", **metadata)
        if min_angle < RENEGADE_ROW_ELBOW_TOP_MIN:
            return _make_error("ELBOW_OVERFLEXION", **metadata)
        return None

    def _register_error_occurrence(self, err: dict) -> None:
        code = err["code"]
        self.error_rep_count[code] = self.error_rep_count.get(code, 0) + 1
        if self.error_rep_count[code] == ERROR_REP_COUNT_THRESHOLD:
            self.confirmed_error_dicts[code] = err

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

        if not required_keypoints_confident(kp, ["shoulder", "elbow", "wrist", "hip"], KEYPOINT_CONFIDENCE_THRESHOLD):
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
        in_mid_zone  = RENEGADE_ROW_DOWN_ANGLE < elbow_angle <= RENEGADE_ROW_UP_ANGLE
        in_up_zone   = elbow_angle <= RENEGADE_ROW_DOWN_ANGLE  # brazo arriba, tirón completo

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
            self._start_pull_attempt(elbow_angle)
        elif self.state == "pulling":
            if in_up_zone:
                self.state = "up"
                self.reps += 1
                self.completed_pull = True
                self.aborted_pull = False
            elif in_down_zone:
                self.state = "down"
                if self.aborted_pull:
                    err = self._build_elbow_top_error()
                    if err is not None:
                        self._register_error_occurrence(err)
                self.aborted_pull = False
        elif self.state == "up" and in_mid_zone:
            self.state = "lowering"
        elif self.state == "lowering" and in_down_zone:
            self.state = "down"
            if self.completed_pull:
                err = self._build_elbow_top_error()
                if err is not None:
                    self._register_error_occurrence(err)
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

        if self.state in ("pulling", "up", "lowering"):
            self._track_pull_attempt(elbow_angle)

        # Hip position checks during active phases
        if self.state in ("pulling", "up", "lowering"):
            if hip_body_angle > RENEGADE_ROW_HIP_SAG_THRESHOLD:
                current_errors_v2.append(_make_error("HIP_SAGGING", hip_body_angle=hip_body_angle))
            elif hip_body_angle < RENEGADE_ROW_HIP_HIGH_THRESHOLD:
                current_errors_v2.append(_make_error("HIP_HIGH", hip_body_angle=hip_body_angle))

        if self.state in ("pulling", "up", "lowering"):
            for err in current_errors_v2:
                code = err["code"]
                self.current_rep_errors[code] = (
                    self.current_rep_errors.get(code, 0) + 1
                )
                self.current_rep_error_dicts[code] = err

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
                "elbow": elbow_angle,
                "hip_body": hip_body_angle,
            },
            "errors": [e["code"] for e in confirmed_errors_v2],
            "errors_v2": confirmed_errors_v2,
            "feedback": feedback_to_send,
        }
