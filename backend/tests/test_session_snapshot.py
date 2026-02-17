import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from session.session_snapshot import build_session_update
from session.session_state import SessionState


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

        for athlete_id, athlete_data in snapshot["athletes"].items():
            self.assertIn("station_id", athlete_data, athlete_id)
            self.assertIn("reps", athlete_data, athlete_id)
            self.assertIn("errors", athlete_data, athlete_id)
            self.assertIsInstance(athlete_data["errors"], list, athlete_id)

        for station_id, station_data in snapshot["stations"].items():
            self.assertIn("exercise", station_data, station_id)


if __name__ == "__main__":
    unittest.main()
