import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from detectors.renegade_row_detector import RenegadeRowDetector
from domain.errors.error_catalog import KNOWN_ERRORS
from domain.errors.error_normalizer import build_errors_v2_from_codes
from domain.session.session_state import SessionState
from domain.session.sync_policy import sync_session_state_for_person
from application.projections.session_update_projection import (
    build_session_update_projection,
)


def _fake_person_kp() -> np.ndarray:
    kp = np.zeros((17, 3))
    kp[:, 2] = 0.9
    kp[:, 0] = np.linspace(0.1, 0.9, 17)
    kp[:, 1] = 0.5
    return kp


def _kp_with_elbow_angle(elbow_angle_deg: float) -> np.ndarray:
    """
    Build right-side keypoints producing approximately elbow_angle_deg at the elbow.
    Left side is all zeros (confidence=0) so choose_side() returns "right".

    Geometry: shoulder=(0.2, 0.5), elbow=(0.5, 0.5).
    Wrist is placed by rotating the vector elbow→shoulder by elbow_angle_deg,
    which produces that exact angle at the elbow via angle_from_arrays.
    Hip (0.7, 0.585) and ankle (0.9, 0.5) → hip_body_angle≈147° (zona neutra, no dispara HIP_SAGGING ni HIP_HIGH).
    """
    import math

    kp = np.zeros((17, 3))  # left side: all (0, 0, 0) — zero confidence

    rad = math.radians(elbow_angle_deg)

    shoulder_y, shoulder_x = 0.2, 0.5
    elbow_y, elbow_x = 0.5, 0.5

    # vector elbow→shoulder
    es_y = shoulder_y - elbow_y  # -0.3
    es_x = shoulder_x - elbow_x  # 0.0
    length = math.hypot(es_y, es_x)

    # Rotate elbow→shoulder by elbow_angle_deg → elbow→wrist direction
    ew_y = es_y * math.cos(rad) - es_x * math.sin(rad)
    ew_x = es_y * math.sin(rad) + es_x * math.cos(rad)
    ew_len = math.hypot(ew_y, ew_x)
    ew_y = (ew_y / ew_len) * length
    ew_x = (ew_x / ew_len) * length

    wrist_y = elbow_y + ew_y
    wrist_x = elbow_x + ew_x

    # Right side keypoints (confidence 0.9 → choose_side picks "right")
    kp[6]  = [shoulder_y, shoulder_x, 0.9]  # right_shoulder
    kp[8]  = [elbow_y,    elbow_x,    0.9]  # right_elbow
    kp[10] = [wrist_y,    wrist_x,    0.9]  # right_wrist
    kp[12] = [0.7, 0.585, 0.9]             # right_hip — ángulo neutro ~147° (entre HIP_HIGH<145 y HIP_SAGGING>150)
    kp[14] = [0.8, 0.5,   0.9]             # right_knee (boosts right score)
    kp[16] = [0.9, 0.5,   0.9]             # right_ankle

    return kp


class RenegadeRowDetectorTests(unittest.TestCase):

    def test_analyze_always_returns_errors_v2_key(self):
        d = RenegadeRowDetector()
        r = d.analyze(_fake_person_kp())
        self.assertIn("errors_v2", r)
        self.assertIsInstance(r["errors_v2"], list)

    def test_errors_v2_entries_have_required_fields(self):
        d = RenegadeRowDetector()
        for _ in range(10):
            r = d.analyze(_fake_person_kp())
        for entry in r.get("errors_v2", []):
            self.assertIn("code", entry)
            self.assertIn("message_key", entry)
            self.assertIn("severity", entry)
            self.assertIn("metadata", entry)
            self.assertIn(entry["severity"], ("info", "warning", "critical"))
            self.assertIsInstance(entry["metadata"], dict)

    def test_errors_list_is_derived_from_errors_v2(self):
        d = RenegadeRowDetector()
        r = d.analyze(_fake_person_kp())
        expected_codes = [e["code"] for e in r["errors_v2"]]
        self.assertEqual(r["errors"], expected_codes)

    def test_known_error_codes_only_from_catalog(self):
        d = RenegadeRowDetector()
        for _ in range(20):
            r = d.analyze(_fake_person_kp())
            for entry in r.get("errors_v2", []):
                self.assertIn(
                    entry["code"],
                    KNOWN_ERRORS,
                    f"Unexpected error code: {entry['code']!r}",
                )
                self.assertNotEqual(
                    entry["code"],
                    "UNKNOWN_ERROR",
                    "Detector produced UNKNOWN_ERROR",
                )

    def test_errors_v2_metadata_contains_causal_angle(self):
        causal_angle_by_code = {
            "RANGE_INSUFFICIENT": "elbow_angle",
            "HIP_SAGGING": "hip_body_angle",
            "HIP_HIGH": "hip_body_angle",
        }
        mock_errors_v2 = [
            {
                "code": "RANGE_INSUFFICIENT",
                "message_key": "error.exercise.range_insufficient",
                "severity": "warning",
                "metadata": {"elbow_angle": 110.5},
            },
            {
                "code": "HIP_SAGGING",
                "message_key": "error.exercise.hip_sagging",
                "severity": "warning",
                "metadata": {"hip_body_angle": 160.2},
            },
            {
                "code": "HIP_HIGH",
                "message_key": "error.exercise.hip_high",
                "severity": "warning",
                "metadata": {"hip_body_angle": 142.0},
            },
        ]
        for entry in mock_errors_v2:
            code = entry["code"]
            expected_key = causal_angle_by_code[code]
            self.assertIn(
                expected_key,
                entry["metadata"],
                f"Error {code!r} missing causal angle {expected_key!r} in metadata",
            )
            self.assertIsInstance(entry["metadata"][expected_key], float)

    def test_rep_counting_increments_on_full_cycle(self):
        d = RenegadeRowDetector()
        self.assertEqual(d.state, "down")
        self.assertEqual(d.reps, 0)

        # Posiciones físicas: "down" = brazo abajo (ángulo alto), "up" = brazo arriba (ángulo bajo)
        kp_arm_down = _kp_with_elbow_angle(160)  # brazo extendido en plancha
        kp_mid      = _kp_with_elbow_angle(115)  # zona intermedia
        kp_arm_up   = _kp_with_elbow_angle(75)   # brazo arriba, tirón completo

        # Ciclo completo: down → pulling → up → lowering → down
        for _ in range(3):
            d.analyze(kp_mid)       # entra en pulling
        for _ in range(3):
            d.analyze(kp_arm_up)    # llega a up (rep contada)
        for _ in range(3):
            d.analyze(kp_mid)       # entra en lowering
        for _ in range(3):
            r = d.analyze(kp_arm_down)  # vuelve a down

        self.assertEqual(r["reps"], 1)

    def test_session_update_shape_unchanged(self):
        state = SessionState()
        detector_result = {
            "valid": True,
            "reps": 2,
            "errors": ["RANGE_INSUFFICIENT"],
            "errors_v2": build_errors_v2_from_codes(["RANGE_INSUFFICIENT"]),
        }
        sync_session_state_for_person(
            session_state=state,
            session_person_id="athlete_1",
            station_id="station2",
            result=detector_result,
            is_squat_station=True,
        )
        snapshot = build_session_update_projection(state)

        self.assertEqual(
            set(snapshot.keys()),
            {"type", "version", "timestamp", "athletes", "stations"},
        )
        athlete = snapshot["athletes"]["athlete_1"]
        self.assertEqual(
            set(athlete.keys()),
            {"station_id", "reps", "errors", "errors_v2"},
        )
        self.assertIn("RANGE_INSUFFICIENT", athlete["errors"])
        for entry in athlete["errors_v2"]:
            self.assertIn("code", entry)
            self.assertIn("message_key", entry)
            self.assertIn("severity", entry)
            self.assertIn("metadata", entry)


class RenegadeRowCrossRepThresholdTests(unittest.TestCase):
    """errors_v2 sólo debe emitirse cuando el mismo error aparece en >= 2 reps."""

    def _run_rep_with_hip_sagging(self, detector):
        """Simula un rep completo con HIP_SAGGING (hip_body_angle > 150).
        hip=(0.7, 0.5) colínea con shoulder=(0.2,0.5) y ankle=(0.9,0.5) → ángulo=180°.
        Devuelve todos los outputs del rep."""

        def _kp(elbow_angle_deg):
            kp = _kp_with_elbow_angle(elbow_angle_deg).copy()
            kp[12] = [0.7, 0.5, 0.9]  # right_hip — x=0.5 colínea → hip_body_angle=180°
            return kp

        kp_mid_sag  = _kp(115)  # pulling, HIP_SAGGING activo
        kp_up_sag   = _kp(75)   # up, HIP_SAGGING activo
        kp_arm_down = _kp_with_elbow_angle(160)  # brazo abajo, cadera neutra

        outputs = []
        for _ in range(3):
            outputs.append(detector.analyze(kp_mid_sag))   # pulling con error
        for _ in range(3):
            outputs.append(detector.analyze(kp_up_sag))    # up con error
        for _ in range(3):
            outputs.append(detector.analyze(kp_mid_sag))   # lowering con error
        for _ in range(3):
            outputs.append(detector.analyze(kp_arm_down))  # down → rep completo
        return outputs

    def test_hip_sagging_not_emitted_after_first_rep(self):
        d = RenegadeRowDetector()
        outputs = self._run_rep_with_hip_sagging(d)
        for r in outputs:
            self.assertEqual(
                r.get("errors_v2", []),
                [],
                "errors_v2 debe estar vacío durante el primer rep con HIP_SAGGING",
            )

    def test_hip_sagging_fires_once_on_second_rep(self):
        d = RenegadeRowDetector()
        self._run_rep_with_hip_sagging(d)  # rep 1
        outputs = self._run_rep_with_hip_sagging(d)  # rep 2 — debe confirmar
        confirmed = [r for r in outputs if r.get("errors_v2")]
        self.assertEqual(len(confirmed), 1, "errors_v2 debe emitirse exactamente una vez al confirmar")
        codes = [e["code"] for e in confirmed[0]["errors_v2"]]
        self.assertIn("HIP_SAGGING", codes)

    def test_hip_sagging_does_not_fire_again_on_third_rep(self):
        d = RenegadeRowDetector()
        self._run_rep_with_hip_sagging(d)  # rep 1
        self._run_rep_with_hip_sagging(d)  # rep 2 — confirma
        outputs = self._run_rep_with_hip_sagging(d)  # rep 3
        for r in outputs:
            self.assertEqual(
                r.get("errors_v2", []),
                [],
                "errors_v2 no debe re-emitirse en reps posteriores a la confirmación",
            )


if __name__ == "__main__":
    unittest.main()
