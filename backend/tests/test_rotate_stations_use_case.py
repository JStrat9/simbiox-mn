import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from application.use_cases.rotate_stations_uc import rotate_stations_use_case
from domain.session.session_state import SessionState


class _RuntimeStationSyncSpy:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def sync(self, session_person_id: str, station_id: str) -> None:
        self.calls.append((session_person_id, station_id))


class RotateStationsUseCaseTests(unittest.TestCase):
    def test_rotate_stations_use_case_rotates_syncs_runtime_and_returns_snapshot(self):
        state = SessionState()
        runtime_sync = _RuntimeStationSyncSpy()

        event = rotate_stations_use_case(
            session_state=state,
            runtime_station_sync=runtime_sync,
        )

        self.assertEqual(event["type"], "SESSION_UPDATE")
        self.assertEqual(state.version, 1)
        self.assertEqual(len(runtime_sync.calls), len(state.assignments))
        self.assertEqual(set(runtime_sync.calls), set(state.assignments.items()))

    def test_rotate_stations_use_case_works_without_runtime_sync(self):
        state = SessionState()

        event = rotate_stations_use_case(session_state=state)

        self.assertEqual(event["type"], "SESSION_UPDATE")
        self.assertEqual(state.version, 1)


if __name__ == "__main__":
    unittest.main()
