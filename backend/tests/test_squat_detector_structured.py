import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from detectors.squat_detector import SquatDetector
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


def _kp_squat(knee_angle_deg: float, hip_angle_deg: float = 80.0) -> np.ndarray:
    """
    Build right-side keypoints that produce the requested knee angle at the knee
    and the requested hip angle (shoulder-hip-knee). Left side has zero confidence
    so choose_side() always picks right.

    Layout (y increases downward, x fixed at 0.5):
      shoulder y=0.2, hip y=0.5, knee at angle from hip, ankle below knee.
    """
    import math

    kp = np.zeros((17, 3))

    # Fix shoulder and hip on the right side
    sh_y, sh_x = 0.2, 0.5
    hi_y, hi_x = 0.5, 0.5

    # Place knee so that hip_angle (shoulder-hip-knee) = hip_angle_deg.
    # Vector hip→shoulder makes angle w.r.t. y-axis; rotate by hip_angle to get hip→knee.
    hi_sh_y = sh_y - hi_y  # -0.3
    hi_sh_x = sh_x - hi_x  # 0.0
    hi_sh_len = math.hypot(hi_sh_y, hi_sh_x)
    hip_rad = math.radians(hip_angle_deg)
    hi_kn_y = hi_sh_y * math.cos(hip_rad) - hi_sh_x * math.sin(hip_rad)
    hi_kn_x = hi_sh_y * math.sin(hip_rad) + hi_sh_x * math.cos(hip_rad)
    hi_kn_len = math.hypot(hi_kn_y, hi_kn_x)
    # normalize and scale to same length as hip→shoulder
    kn_y = hi_y + (hi_kn_y / hi_kn_len) * hi_sh_len
    kn_x = hi_x + (hi_kn_x / hi_kn_len) * hi_sh_len

    # Place ankle so that knee_angle (hip-knee-ankle) = knee_angle_deg.
    kn_hi_y = hi_y - kn_y
    kn_hi_x = hi_x - kn_x
    kn_hi_len = math.hypot(kn_hi_y, kn_hi_x)
    knee_rad = math.radians(knee_angle_deg)
    kn_an_y = kn_hi_y * math.cos(knee_rad) - kn_hi_x * math.sin(knee_rad)
    kn_an_x = kn_hi_y * math.sin(knee_rad) + kn_hi_x * math.cos(knee_rad)
    kn_an_len = math.hypot(kn_an_y, kn_an_x)
    an_y = kn_y + (kn_an_y / kn_an_len) * kn_hi_len
    an_x = kn_x + (kn_an_x / kn_an_len) * kn_hi_len

    conf = 0.9
    kp[6]  = [sh_y, sh_x, conf]  # right_shoulder
    kp[12] = [hi_y, hi_x, conf]  # right_hip
    kp[14] = [kn_y, kn_x, conf]  # right_knee
    kp[16] = [an_y, an_x, conf]  # right_ankle

    return kp


class SquatDetectorStructuredOutputTests(unittest.TestCase):

    def test_analyze_always_returns_errors_v2_key(self):
        d = SquatDetector()
        r = d.analyze(_fake_person_kp())
        self.assertIn("errors_v2", r)
        self.assertIsInstance(r["errors_v2"], list)

    def test_errors_v2_empty_when_no_errors_detected(self):
        d = SquatDetector()
        r = d.analyze(_fake_person_kp())
        # Synthetic keypoints produce neutral geometry — no errors expected
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["errors_v2"], [])

    def test_errors_v2_entries_have_required_fields(self):
        d = SquatDetector()
        # Run several frames to increase chance of hitting an error
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
        d = SquatDetector()
        r = d.analyze(_fake_person_kp())
        expected_codes = [e["code"] for e in r["errors_v2"]]
        self.assertEqual(r["errors"], expected_codes)

    def test_known_error_codes_only_from_catalog(self):
        d = SquatDetector()
        for _ in range(10):
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
                    "Detector produced UNKNOWN_ERROR — likely a raw text string escaped.",
                )

    def test_errors_v2_metadata_contains_causal_angle(self):
        # Build a result that forces known errors by constructing it directly
        # with the same interface the sync_policy will see.
        causal_angle_by_code = {
            "DEPTH_INSUFFICIENT": "knee_angle",
            "DEPTH_EXCESSIVE": "knee_angle",
            "BACK_ROUNDED": "hip_angle",
            "KNEE_FORWARD": "ankle_angle",
        }
        # Inject a mock detector result as if the detector fired these errors
        mock_errors_v2 = [
            {
                "code": "BACK_ROUNDED",
                "message_key": "error.squat.back_rounded",
                "severity": "warning",
                "metadata": {"hip_angle": 45.5},
            },
            {
                "code": "KNEE_FORWARD",
                "message_key": "error.squat.knee_forward",
                "severity": "warning",
                "metadata": {"ankle_angle": 130.2},
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

    def test_detector_errors_never_contain_spanish_text(self):
        spanish_texts = {
            "no bajas lo suficiente",
            "baja demasiado",
            "espalda encorvada",
            "rodillas adelantadas",
        }
        d = SquatDetector()
        for _ in range(20):
            r = d.analyze(_fake_person_kp())
            for err in r.get("errors", []):
                self.assertNotIn(
                    str(err).lower(),
                    spanish_texts,
                    f"Spanish text found in errors: {err!r}",
                )

    def test_sync_policy_takes_direct_errors_v2_path(self):
        state = SessionState()
        detector_result = {
            "valid": True,
            "reps": 1,
            "errors": ["DEPTH_INSUFFICIENT"],
            "errors_v2": [
                {
                    "code": "DEPTH_INSUFFICIENT",
                    "message_key": "error.squat.depth_insufficient",
                    "severity": "warning",
                    "metadata": {"knee_angle": 85.0},
                }
            ],
        }
        changed = sync_session_state_for_person(
            session_state=state,
            session_person_id="athlete_1",
            station_id="station1",
            result=detector_result,
            is_squat_station=True,
        )
        self.assertTrue(changed)
        self.assertEqual(state.errors["athlete_1"], ["DEPTH_INSUFFICIENT"])
        stored = state.errors_v2["athlete_1"]
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["code"], "DEPTH_INSUFFICIENT")
        self.assertEqual(stored[0]["metadata"], {"knee_angle": 85.0})

    def test_session_update_shape_unchanged_end_to_end(self):
        state = SessionState()
        detector_result = {
            "valid": True,
            "reps": 3,
            "errors": ["BACK_ROUNDED", "KNEE_FORWARD"],
            "errors_v2": build_errors_v2_from_codes(["BACK_ROUNDED", "KNEE_FORWARD"]),
        }
        sync_session_state_for_person(
            session_state=state,
            session_person_id="athlete_1",
            station_id="station1",
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
        # errors_v2 sorted alphabetically by code: BACK_ROUNDED < KNEE_FORWARD
        self.assertEqual(athlete["errors"], [e["code"] for e in athlete["errors_v2"]])
        self.assertIn("BACK_ROUNDED", athlete["errors"])
        self.assertIn("KNEE_FORWARD", athlete["errors"])
        for entry in athlete["errors_v2"]:
            self.assertIn("code", entry)
            self.assertIn("message_key", entry)
            self.assertIn("severity", entry)
            self.assertIn("metadata", entry)


class SquatDetectorCrossRepThresholdTests(unittest.TestCase):
    """errors_v2 sólo debe emitirse cuando el mismo error aparece en >= 2 reps."""

    def _run_squat_rep_with_back_rounded(self, detector):
        """Simula un rep completo con BACK_ROUNDED (hip_angle=40 < LEAN_THRESHOLD=60).
        Devuelve todos los outputs del rep."""
        # Keypoints: zona de bajada con espalda curvada (hip_angle=40)
        kp_down_error = _kp_squat(knee_angle_deg=60, hip_angle_deg=40)
        # Zona de pie (knee>120 → in_up_zone), sin error
        kp_up = _kp_squat(knee_angle_deg=150, hip_angle_deg=80)
        # Zona intermedia (90 < knee <= 120)
        kp_mid = _kp_squat(knee_angle_deg=100, hip_angle_deg=80)

        outputs = []
        # up → descending
        outputs.append(detector.analyze(kp_mid))
        # descending → down (knee=60 dentro de PERFECT_DEPTH_MIN..MAX por defecto 50-69)
        for _ in range(3):
            outputs.append(detector.analyze(kp_down_error))
        # down → ascending
        outputs.append(detector.analyze(kp_mid))
        # ascending → up
        outputs.append(detector.analyze(kp_up))
        return outputs

    def test_error_not_emitted_after_first_rep(self):
        d = SquatDetector()
        outputs = self._run_squat_rep_with_back_rounded(d)
        for r in outputs:
            self.assertEqual(
                r.get("errors_v2", []),
                [],
                "errors_v2 debe estar vacío durante el primer rep con error",
            )

    def test_error_fires_once_on_second_rep(self):
        d = SquatDetector()
        # Rep 1 — sin confirmación
        self._run_squat_rep_with_back_rounded(d)
        # Rep 2 — debe confirmar
        outputs = self._run_squat_rep_with_back_rounded(d)
        confirmed = [r for r in outputs if r.get("errors_v2")]
        self.assertEqual(len(confirmed), 1, "errors_v2 debe emitirse exactamente una vez al confirmar")
        codes = [e["code"] for e in confirmed[0]["errors_v2"]]
        self.assertIn("BACK_ROUNDED", codes)

    def test_error_does_not_fire_again_on_third_rep(self):
        d = SquatDetector()
        self._run_squat_rep_with_back_rounded(d)  # rep 1
        self._run_squat_rep_with_back_rounded(d)  # rep 2 — confirma
        outputs = self._run_squat_rep_with_back_rounded(d)  # rep 3
        for r in outputs:
            self.assertEqual(
                r.get("errors_v2", []),
                [],
                "errors_v2 no debe re-emitirse en reps posteriores a la confirmación",
            )


if __name__ == "__main__":
    unittest.main()
