import json
import re
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from communication import websocket_server
from session.session_state import SessionState


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


class WebSocketPhase2ContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        websocket_server.connected_clients.clear()
        websocket_server.register_rotate_station_handler(
            lambda session_person_id, station_id: None
        )
        state = SessionState()
        websocket_server.register_session_state(state)

    async def test_initial_connection_sends_only_session_update(self):
        ws = FakeWebSocket(incoming_messages=[])

        await websocket_server.handler(ws)

        self.assertEqual(len(ws.sent_payloads), 1)
        self.assertEqual(ws.sent_payloads[0]["type"], "SESSION_UPDATE")
        self.assertNotIn("assignments", ws.sent_payloads[0])
        self.assertNotIn("rotation", ws.sent_payloads[0])

    async def test_rotate_stations_broadcasts_only_session_update(self):
        rotate_msg = json.dumps({"type": "ROTATE_STATIONS"})
        ws = FakeWebSocket(incoming_messages=[rotate_msg])

        await websocket_server.handler(ws)

        self.assertEqual(len(ws.sent_payloads), 2)
        first, second = ws.sent_payloads
        self.assertEqual(first["type"], "SESSION_UPDATE")
        self.assertEqual(second["type"], "SESSION_UPDATE")
        self.assertGreater(second["version"], first["version"])

    async def test_transport_uses_public_athlete_identity(self):
        ws = FakeWebSocket(incoming_messages=[])

        await websocket_server.handler(ws)

        snapshot = ws.sent_payloads[0]
        for athlete_id in snapshot["athletes"].keys():
            self.assertRegex(athlete_id, r"^athlete_\d+$")
            self.assertFalse(re.match(r"^(person|client|track)_", athlete_id))

    async def test_transport_includes_errors_v2_and_legacy_errors_derivation(self):
        ws = FakeWebSocket(incoming_messages=[])

        await websocket_server.handler(ws)

        snapshot = ws.sent_payloads[0]
        for athlete_id, athlete_data in snapshot["athletes"].items():
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

    async def test_invalid_json_is_ignored_without_extra_broadcast(self):
        ws = FakeWebSocket(incoming_messages=["{invalid-json"])

        await websocket_server.handler(ws)

        # Only initial snapshot should be sent.
        self.assertEqual(len(ws.sent_payloads), 1)
        self.assertEqual(ws.sent_payloads[0]["type"], "SESSION_UPDATE")

    async def test_unknown_message_type_is_ignored_without_extra_broadcast(self):
        unknown_msg = json.dumps({"type": "UNKNOWN_EVENT"})
        ws = FakeWebSocket(incoming_messages=[unknown_msg])

        await websocket_server.handler(ws)

        # Only initial snapshot should be sent.
        self.assertEqual(len(ws.sent_payloads), 1)
        self.assertEqual(ws.sent_payloads[0]["type"], "SESSION_UPDATE")


if __name__ == "__main__":
    unittest.main()
