import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from application.projections.session_update_projection import (
    build_session_update_projection,
)
from session.session_snapshot import build_session_update
from session.session_state import SessionState


class SessionSnapshotShimTests(unittest.TestCase):
    def test_legacy_session_snapshot_shim_matches_application_projection(self):
        state = SessionState()
        state.set_assignment("athlete_1", "station2", increment_version=True)
        state.set_reps("athlete_1", 3, increment_version=True)
        state.set_errors("athlete_1", ["KNEE_FORWARD"], increment_version=True)

        from_shim = build_session_update(state)
        from_projection = build_session_update_projection(state)

        self.assertEqual(from_shim, from_projection)


if __name__ == "__main__":
    unittest.main()
