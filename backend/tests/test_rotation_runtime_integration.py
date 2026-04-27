import json
import inspect
import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from communication import websocket_server
from domain.session.session_state import SessionState
from interfaces.runtime.session_person_manager import SessionPersonManager


class FakeWebSocket:
    def __init__(self, incoming_messages: list[str]):
        self.remote_address = ("127.0.0.1", 12345)
        self._incoming = list(incoming_messages)
        self.sent_payloads: list[dict] = []

    async def send(self, payload: str):
        self.sent_payloads.append(json.loads(payload))

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)


class RotationRuntimeIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        websocket_server.connected_clients.clear()
        websocket_server.register_rotate_station_handler(None)
        websocket_server.register_clear_reviewed_errors_handler(None)
        self.state = SessionState()
        websocket_server.register_session_state(self.state)

    async def test_ws_handler_delegates_rotation_to_use_case(self):
        source = inspect.getsource(websocket_server)
        self.assertIn("rotate_stations_use_case", source)
        self.assertNotIn("from session.rotation import rotate_stations", source)
        self.assertIn("build_session_update_projection", source)
        self.assertNotIn("from session.session_snapshot import build_session_update", source)

    async def test_rotate_calls_runtime_handler_for_each_assignment(self):
        calls: list[tuple[str, str]] = []

        def runtime_handler(session_person_id: str, station_id: str):
            calls.append((session_person_id, station_id))

        websocket_server.register_rotate_station_handler(runtime_handler)

        ws = FakeWebSocket([json.dumps({"type": "ROTATE_STATIONS"})])
        await websocket_server.handler(ws)

        self.assertEqual(self.state.version, 1)
        self.assertEqual(len(ws.sent_payloads), 2)
        self.assertEqual(len(calls), len(self.state.assignments))
        self.assertEqual(set(calls), set(self.state.assignments.items()))

    async def test_rotate_keeps_manager_runtime_station_in_sync(self):
        manager = SessionPersonManager(max_persons=6, distance_threshold=120.0)
        manager.session_state = self.state

        _, athlete_id = manager.resolve_identity(np.array([10.0, 20.0]))
        before_station = manager.get_station(athlete_id).station_id
        self.assertEqual(before_station, "station1")

        websocket_server.register_rotate_station_handler(manager.assign_station)

        ws = FakeWebSocket([json.dumps({"type": "ROTATE_STATIONS"})])
        await websocket_server.handler(ws)

        after_station_runtime = manager.get_station(athlete_id).station_id
        after_station_state = self.state.assignments[athlete_id]

        self.assertEqual(self.state.version, 1)
        self.assertEqual(after_station_runtime, "station2")
        self.assertEqual(after_station_state, "station2")

    async def test_clear_reviewed_errors_calls_runtime_handler_for_each_assignment(self):
        calls: list[str] = []

        def clear_handler(session_person_id: str):
            calls.append(session_person_id)

        self.state.set_errors_v2(
            "athlete_1",
            [
                {
                    "code": "BACK_ROUNDED",
                    "message_key": "error.squat.back_rounded",
                    "severity": "warning",
                    "metadata": {"hip_angle": 40.0},
                }
            ],
            increment_version=False,
        )

        websocket_server.register_clear_reviewed_errors_handler(clear_handler)

        ws = FakeWebSocket([json.dumps({"type": "CLEAR_REVIEWED_ERRORS"})])
        await websocket_server.handler(ws)

        self.assertEqual(len(ws.sent_payloads), 2)
        self.assertEqual(len(calls), len(self.state.assignments))
        self.assertEqual(set(calls), set(self.state.assignments.keys()))


if __name__ == "__main__":
    unittest.main()
