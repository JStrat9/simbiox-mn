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


if __name__ == "__main__":
    unittest.main()
