# communication/websocket_server.py

import asyncio
import json

import websockets

from typing import Dict, Set

from application.projections.session_update_projection import (
    build_session_update_projection,
)
from application.ports.runtime_reviewed_errors_sync import (
    RuntimeReviewedErrorsSyncPort,
)
from application.ports.runtime_station_sync import RuntimeStationSyncPort
from application.use_cases.clear_reviewed_errors_uc import (
    clear_reviewed_errors_use_case,
)
from application.use_cases.rotate_stations_uc import rotate_stations_use_case
from domain.session.session_state import SessionState


connected_clients: Set[websockets.WebSocketServerProtocol] = set()
server_loop: asyncio.AbstractEventLoop | None = None

_rotate_station_handler = None
_clear_reviewed_errors_handler = None
session_state = SessionState()


def register_rotate_station_handler(handler):
    global _rotate_station_handler
    _rotate_station_handler = handler


def register_clear_reviewed_errors_handler(handler):
    global _clear_reviewed_errors_handler
    _clear_reviewed_errors_handler = handler


def register_session_state(state: SessionState):
    global session_state
    session_state = state


# -----------------------------
# Core WebSocket handler
# -----------------------------
async def handler(websocket, path=None):
    print(
        f"[WS] Client connected: {getattr(websocket, 'remote_address', None)}",
        flush=True,
    )
    connected_clients.add(websocket)

    await websocket.send(json.dumps(build_session_update_projection(session_state)))

    try:
        async for message in websocket:
            print("[WS] Received from client:", message, flush=True)

            try:
                msg = json.loads(message)
            except json.JSONDecodeError:
                print("[WS][WARN] Invalid JSON", flush=True)
                continue

            if msg.get("type") == "ROTATE_STATIONS":
                runtime_station_sync = _build_runtime_station_sync_adapter()
                event = rotate_stations_use_case(
                    session_state=session_state,
                    runtime_station_sync=runtime_station_sync,
                )
                await broadcast(event)
            elif msg.get("type") == "CLEAR_REVIEWED_ERRORS":
                runtime_reviewed_errors_sync = (
                    _build_runtime_reviewed_errors_sync_adapter()
                )
                event = clear_reviewed_errors_use_case(
                    session_state=session_state,
                    runtime_reviewed_errors_sync=runtime_reviewed_errors_sync,
                )
                await broadcast(event)

    except Exception as e:
        print("[WS] Handler exception:", e, flush=True)
    finally:
        connected_clients.discard(websocket)
        print(
            f"[WS] Client disconnected: {getattr(websocket, 'remote_address', None)}",
            flush=True,
        )


# -----------------------------
# Event emitters (DOMAIN EVENTS)
# -----------------------------
async def broadcast(event: Dict):
    if not connected_clients:
        print("[WS] No connected clients, skipping broadcast", flush=True)
        return

    msg = json.dumps(event)

    coros = [ws.send(msg) for ws in list(connected_clients)]
    results = await asyncio.gather(*coros, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            print("[WS] Failed to send message:", result, flush=True)


def emit_session_update():
    """Emit canonical SESSION_UPDATE snapshot."""

    if server_loop is None:
        print("[WS] emit_session_update: server_loop not ready", flush=True)
        return

    event = build_session_update_projection(session_state)
    asyncio.run_coroutine_threadsafe(broadcast(event), server_loop)


class _FunctionRuntimeStationSyncAdapter(RuntimeStationSyncPort):
    def __init__(self, handler):
        self._handler = handler

    def sync(self, session_person_id: str, station_id: str) -> None:
        self._handler(session_person_id, station_id)


def _build_runtime_station_sync_adapter() -> RuntimeStationSyncPort | None:
    if _rotate_station_handler is None:
        return None
    return _FunctionRuntimeStationSyncAdapter(_rotate_station_handler)


class _FunctionRuntimeReviewedErrorsSyncAdapter(RuntimeReviewedErrorsSyncPort):
    def __init__(self, handler):
        self._handler = handler

    def clear(self, session_person_id: str) -> None:
        self._handler(session_person_id)


def _build_runtime_reviewed_errors_sync_adapter(
) -> RuntimeReviewedErrorsSyncPort | None:
    if _clear_reviewed_errors_handler is None:
        return None
    return _FunctionRuntimeReviewedErrorsSyncAdapter(
        _clear_reviewed_errors_handler
    )


# -----------------------------
# Server bootstrap
# -----------------------------
async def start_server(host: str = "0.0.0.0", port: int = 8765, ready_event=None):
    global server_loop
    server_loop = asyncio.get_running_loop()

    print(
        f"[WS] Starting server on ws://{host}:{port} (loop id={id(server_loop)})",
        flush=True,
    )

    server = await websockets.serve(handler, host, port)

    if ready_event:
        ready_event.set()
        print("[WS] Server ready", flush=True)

    await server.wait_closed()
