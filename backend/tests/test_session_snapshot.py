import sys
import re
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from application.projections.session_update_projection import (
    build_session_update_projection as build_session_update,
)
from domain.session.session_state import SessionState


class SessionSnapshotTests(unittest.TestCase):
    def test_build_session_update_schema_and_content(self):
        state = SessionState()
        state.set_assignment("athlete_1", "station2", increment_version=True)
        state.set_reps("athlete_1", 7, increment_version=True)
        state.set_errors(
            "athlete_1",
            ["DEPTH_INSUFFICIENT", "KNEE_FORWARD"],
            increment_version=True,
        )

        snapshot = build_session_update(state)

        self.assertEqual(
            set(snapshot.keys()),
            {"type", "version", "timestamp", "athletes", "stations"},
        )
        self.assertEqual(snapshot["type"], "SESSION_UPDATE")
        self.assertIsInstance(snapshot["version"], int)
        self.assertGreaterEqual(snapshot["version"], 1)
        self.assertIsInstance(snapshot["timestamp"], int)

        self.assertIn("athletes", snapshot)
        self.assertIn("stations", snapshot)
        self.assertIn("athlete_1", snapshot["athletes"])

        athlete_1 = snapshot["athletes"]["athlete_1"]
        self.assertEqual(athlete_1["station_id"], "station2")
        self.assertEqual(athlete_1["reps"], 7)
        self.assertEqual(
            athlete_1["errors"], ["DEPTH_INSUFFICIENT", "KNEE_FORWARD"]
        )
        self.assertEqual(
            athlete_1["errors_v2"],
            [
                {
                    "code": "DEPTH_INSUFFICIENT",
                    "message_key": "error.squat.depth_insufficient",
                    "severity": "warning",
                    "metadata": {},
                },
                {
                    "code": "KNEE_FORWARD",
                    "message_key": "error.squat.knee_forward",
                    "severity": "warning",
                    "metadata": {},
                },
            ],
        )

        for athlete_id, athlete_data in snapshot["athletes"].items():
            self.assertEqual(
                set(athlete_data.keys()),
                {"station_id", "reps", "errors", "errors_v2"},
                athlete_id,
            )
            self.assertIn("station_id", athlete_data, athlete_id)
            self.assertIn("reps", athlete_data, athlete_id)
            self.assertIn("errors", athlete_data, athlete_id)
            self.assertIn("errors_v2", athlete_data, athlete_id)
            self.assertIsInstance(athlete_data["errors"], list, athlete_id)
            self.assertIsInstance(athlete_data["errors_v2"], list, athlete_id)
            self.assertEqual(
                athlete_data["errors"],
                [error["code"] for error in athlete_data["errors_v2"]],
                athlete_id,
            )
            for error in athlete_data["errors_v2"]:
                self.assertIn("code", error, athlete_id)
                self.assertIn("message_key", error, athlete_id)
                self.assertIn("severity", error, athlete_id)
                self.assertIn("metadata", error, athlete_id)

        for station_id, station_data in snapshot["stations"].items():
            self.assertEqual(set(station_data.keys()), {"exercise"}, station_id)
            self.assertIn("exercise", station_data, station_id)

    def test_snapshot_derives_legacy_errors_from_errors_v2(self):
        state = SessionState()
        state.set_errors_v2(
            "athlete_1",
            [
                {
                    "code": "KNEE_FORWARD",
                    "message_key": "error.squat.knee_forward",
                    "severity": "critical",
                    "metadata": {"frames": 4},
                }
            ],
            increment_version=False,
        )

        snapshot = build_session_update(state)
        athlete_1 = snapshot["athletes"]["athlete_1"]

        self.assertEqual(athlete_1["errors"], ["KNEE_FORWARD"])
        self.assertEqual(
            athlete_1["errors_v2"],
            [
                {
                    "code": "KNEE_FORWARD",
                    "message_key": "error.squat.knee_forward",
                    "severity": "critical",
                    "metadata": {"frames": 4},
                }
            ],
        )

    def test_snapshot_exposes_only_public_athlete_identity(self):
        state = SessionState()
        snapshot = build_session_update(state)

        for athlete_id in snapshot["athletes"].keys():
            self.assertRegex(athlete_id, r"^athlete_\d+$")
            self.assertFalse(re.match(r"^(person|client|track)_", athlete_id))


if __name__ == "__main__":
    unittest.main()
