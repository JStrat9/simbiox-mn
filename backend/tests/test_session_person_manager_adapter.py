import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from interfaces.runtime.session_person_manager_adapter import (
    LegacySessionPersonManagerAdapter,
    build_legacy_session_person_manager_adapter,
)
from interfaces.runtime.session_person_manager import SessionPersonManager
from domain.session.session_state import SessionState


class SessionPersonManagerAdapterTests(unittest.TestCase):
    def test_adapter_resolve_returns_identity_resolution_dataclass(self):
        state = SessionState()
        manager = SessionPersonManager(max_persons=6, distance_threshold=120.0)
        manager.session_state = state
        adapter = LegacySessionPersonManagerAdapter(manager)

        resolution = adapter.resolve(np.array([10.0, 20.0]))

        self.assertEqual(resolution.client_id, "1")
        self.assertEqual(resolution.session_person_id, "athlete_1")

    def test_builder_wires_session_state_and_station_sync_methods(self):
        state = SessionState()
        adapter = build_legacy_session_person_manager_adapter(
            session_state=state,
            max_persons=6,
            distance_threshold=120.0,
        )

        resolution = adapter.resolve(np.array([10.0, 20.0]))
        station_before = adapter.get_station(resolution.session_person_id)
        self.assertEqual(station_before.station_id, "station1")

        adapter.assign_station(resolution.session_person_id, "station2")
        station_after = adapter.get_station(resolution.session_person_id)
        self.assertEqual(station_after.station_id, "station2")

        adapter.release_missing_client_ids(set())


if __name__ == "__main__":
    unittest.main()
