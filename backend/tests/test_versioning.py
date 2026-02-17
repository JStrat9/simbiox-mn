import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from session.rotation import rotate_stations
from session.session_state import SessionState


class SessionVersioningTests(unittest.TestCase):
    def test_version_only_increases_for_observable_changes(self):
        state = SessionState()
        initial_version = state.version

        # No observable change -> no version increment.
        state.set_reps("athlete_1", 0, increment_version=True)
        state.set_errors("athlete_1", [], increment_version=True)
        state.set_assignment("athlete_1", "station1", increment_version=True)
        self.assertEqual(state.version, initial_version)

        # Observable changes -> monotonic increments.
        state.set_reps("athlete_1", 1, increment_version=True)
        self.assertEqual(state.version, initial_version + 1)

        state.set_errors("athlete_1", ["DEPTH_INSUFFICIENT"], increment_version=True)
        self.assertEqual(state.version, initial_version + 2)

        state.set_assignment("athlete_1", "station2", increment_version=True)
        self.assertEqual(state.version, initial_version + 3)

        rotate_stations(state)
        self.assertEqual(state.version, initial_version + 4)
        self.assertEqual(state.rotation_index, 1)

    def test_version_does_not_increase_when_increment_flag_is_false(self):
        state = SessionState()
        initial_version = state.version

        state.set_reps("athlete_1", 10, increment_version=False)
        state.set_errors("athlete_1", ["KNEE_FORWARD"], increment_version=False)
        state.set_assignment("athlete_1", "station2", increment_version=False)

        self.assertEqual(state.version, initial_version)


if __name__ == "__main__":
    unittest.main()
