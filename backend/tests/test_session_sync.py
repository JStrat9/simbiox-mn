import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from session.session_state import SessionState
from session.session_sync import sync_session_state_for_person


class SessionSyncTests(unittest.TestCase):
    def setUp(self):
        self.state = SessionState()
        self.athlete_id = "athlete_1"

    def test_no_op_returns_false_and_keeps_version(self):
        changed = sync_session_state_for_person(
            session_state=self.state,
            session_person_id=self.athlete_id,
            station_id="station1",
            result={"valid": True, "reps": 0, "errors": []},
            is_squat_station=True,
        )

        self.assertFalse(changed)
        self.assertEqual(self.state.version, 0)

    def test_assignment_change_returns_true_and_increments_version(self):
        changed = sync_session_state_for_person(
            session_state=self.state,
            session_person_id=self.athlete_id,
            station_id="station2",
            result={"valid": True, "reps": 0, "errors": []},
            is_squat_station=False,
        )

        self.assertTrue(changed)
        self.assertEqual(self.state.assignments[self.athlete_id], "station2")
        self.assertEqual(self.state.version, 1)

    def test_non_squat_clears_errors(self):
        self.state.set_errors(self.athlete_id, ["KNEE_FORWARD"], increment_version=False)

        changed = sync_session_state_for_person(
            session_state=self.state,
            session_person_id=self.athlete_id,
            station_id="station1",
            result={"valid": True, "reps": 0, "errors": ["SHOULD_NOT_APPLY"]},
            is_squat_station=False,
        )

        self.assertTrue(changed)
        self.assertEqual(self.state.errors[self.athlete_id], [])
        self.assertEqual(self.state.version, 1)

    def test_squat_valid_updates_reps_and_normalized_errors(self):
        changed = sync_session_state_for_person(
            session_state=self.state,
            session_person_id=self.athlete_id,
            station_id="station1",
            result={
                "valid": True,
                "reps": 3,
                "errors": ["DEPTH_INSUFFICIENT", "DEPTH_INSUFFICIENT"],
            },
            is_squat_station=True,
        )

        self.assertTrue(changed)
        self.assertEqual(self.state.reps[self.athlete_id], 3)
        self.assertEqual(self.state.errors[self.athlete_id], ["DEPTH_INSUFFICIENT"])
        self.assertEqual(self.state.version, 2)

        changed_again = sync_session_state_for_person(
            session_state=self.state,
            session_person_id=self.athlete_id,
            station_id="station1",
            result={
                "valid": True,
                "reps": 3,
                "errors": ["DEPTH_INSUFFICIENT"],
            },
            is_squat_station=True,
        )

        self.assertFalse(changed_again)
        self.assertEqual(self.state.version, 2)

    def test_squat_invalid_does_not_change_reps_or_errors(self):
        self.state.set_reps(self.athlete_id, 2, increment_version=False)
        self.state.set_errors(self.athlete_id, ["KNEE_FORWARD"], increment_version=False)

        changed = sync_session_state_for_person(
            session_state=self.state,
            session_person_id=self.athlete_id,
            station_id="station1",
            result={"valid": False, "reps": 99, "errors": ["DEPTH_INSUFFICIENT"]},
            is_squat_station=True,
        )

        self.assertFalse(changed)
        self.assertEqual(self.state.reps[self.athlete_id], 2)
        self.assertEqual(self.state.errors[self.athlete_id], ["KNEE_FORWARD"])
        self.assertEqual(self.state.version, 0)


if __name__ == "__main__":
    unittest.main()
