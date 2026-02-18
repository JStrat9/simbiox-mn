import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from session.rotation import rotate_stations
from session.session_snapshot import build_session_update
from session.session_state import SessionState


class MainRuntimeContractTests(unittest.TestCase):
    def test_snapshot_version_and_timestamp_track_observable_change(self):
        state = SessionState()
        before = build_session_update(state)

        # No observable change: value remains the same.
        state.set_reps("athlete_1", 0, increment_version=True)
        same = build_session_update(state)
        self.assertEqual(same["version"], before["version"])
        self.assertEqual(same["timestamp"], before["timestamp"])

        # Observable change: reps changes.
        state.set_reps("athlete_1", 1, increment_version=True)
        changed = build_session_update(state)
        self.assertGreater(changed["version"], before["version"])
        self.assertGreaterEqual(changed["timestamp"], before["timestamp"])

    def test_rotate_stations_updates_snapshot_once_per_effective_rotation(self):
        state = SessionState()
        before = build_session_update(state)

        rotate_stations(state)
        after = build_session_update(state)

        self.assertEqual(after["version"], before["version"] + 1)
        self.assertEqual(state.rotation_index, 1)

        # Rotation must preserve one-to-one station assignment cardinality.
        station_ids = [a["station_id"] for a in after["athletes"].values()]
        self.assertEqual(len(station_ids), len(set(station_ids)))


if __name__ == "__main__":
    unittest.main()
