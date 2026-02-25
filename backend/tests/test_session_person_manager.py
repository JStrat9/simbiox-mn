import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.session.session_state import SessionState
from interfaces.runtime.session_person_manager import SessionPersonManager


class SessionPersonManagerIdentityTests(unittest.TestCase):
    def setUp(self):
        self.manager = SessionPersonManager(
            max_persons=2,
            reassignment_timeout=2.0,
            t_active=0.8,
            t_lost=2.5,
            distance_threshold=120.0,
        )
        self.manager.session_state = SessionState()

    def test_reassignment_keeps_same_athlete_after_temporary_loss(self):
        c1, athlete_1 = self.manager.resolve_identity(np.array([10.0, 10.0]))
        self.assertEqual(athlete_1, "athlete_1")

        # No detections this frame -> physical client id is released.
        self.manager.release_missing_client_ids(set())

        c2, athlete_after_reappear = self.manager.resolve_identity(np.array([12.0, 11.0]))
        self.assertEqual(athlete_after_reappear, athlete_1)
        self.assertNotEqual(c1, c2)

    def test_far_second_person_gets_new_athlete_identity(self):
        _, athlete_1 = self.manager.resolve_identity(np.array([10.0, 10.0]))
        _, athlete_2 = self.manager.resolve_identity(np.array([400.0, 400.0]))

        self.assertEqual(athlete_1, "athlete_1")
        self.assertEqual(athlete_2, "athlete_2")
        self.assertNotEqual(athlete_1, athlete_2)


if __name__ == "__main__":
    unittest.main()
