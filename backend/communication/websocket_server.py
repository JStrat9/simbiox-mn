# communication/websocket_server.py

import asyncio
import json

import websockets

from typing import Dict, Set

from session.rotation import rotate_stations
from session.session_snapshot import build_session_update
from session.session_state import SessionState


connected_clients: Set[websockets.WebSocketServerProtocol] = set()
server_loop: asyncio.AbstractEventLoop | None = None

_rotate_station_handler = None
session_state = SessionState()


def register_rotate_station_handler(handler):
    global _rotate_station_handler
    _rotate_station_handler = handler


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

    await websocket.send(json.dumps(build_session_update(session_state)))

    try:
        async for message in websocket:
            print("[WS] Received from client:", message, flush=True)

            try:
                msg = json.loads(message)
            except json.JSONDecodeError:
                print("[WS][WARN] Invalid JSON", flush=True)
                continue

            if msg.get("type") == "ROTATE_STATIONS":
                new_assignments = rotate_stations(session_state)
                print("[DEBUG ROTATE STATIONS] New assignments:", new_assignments, flush=True)
                _apply_rotation_to_runtime(new_assignments)

                await broadcast(build_session_update(session_state))

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

    event = build_session_update(session_state)
    asyncio.run_coroutine_threadsafe(broadcast(event), server_loop)


def _apply_rotation_to_runtime(assignments: Dict[str, str]):
    """
    Keep runtime station view in sync after canonical rotation.
    """
    if _rotate_station_handler is None:
        print("[WS][WARN] rotate station handler not registered", flush=True)
        return

    for session_person_id, station_id in assignments.items():
        _rotate_station_handler(session_person_id, station_id)


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
