import asyncio
import time
import threading

from communication.websocket_server import (
    emit_session_update,
    start_server,
    register_rotate_station_handler,
    register_session_state,
)
from application.ports.session_person_manager_ports import RuntimeSessionManagerPort
from config import MAX_PERSONS
from domain.session.session_state import SessionState
from interfaces.runtime.session_person_manager_adapter import (
    build_legacy_session_person_manager_adapter,
)
from runtime.app_runtime import run_app_runtime
from runtime.perf_monitor import PsutilPerfReporter
from runtime.visualization import OpenCVFramePresenter, OpenCVKeypressControl

session_state = SessionState()
session_manager: RuntimeSessionManagerPort = build_legacy_session_person_manager_adapter(
    session_state=session_state,
    max_persons=MAX_PERSONS,
    t_active=0.8,
    t_lost=2.0,
    distance_threshold=120.0,
)
register_session_state(session_state)


def on_rotate_station(session_person_id: str, station_id: str):
    session_manager.assign_station(session_person_id, station_id)

    print(
        f"[SESSION][ROTATION_SYNC] "
        f"{session_person_id} -> {station_id}",
        flush=True,
    )


register_rotate_station_handler(on_rotate_station)


class WebSocketSessionUpdatePublisher:
    def publish(self) -> None:
        emit_session_update()


def main():
    print("[INFO][BOOT] Starting runtime...", flush=True)
    run_app_runtime(
        session_state=session_state,
        session_manager=session_manager,
        frame_presenter=OpenCVFramePresenter(window_name="Side Camera"),
        runtime_control=OpenCVKeypressControl(quit_key="q", wait_ms=1),
        perf_reporter=PsutilPerfReporter(label="MAIN"),
        session_update_publisher=WebSocketSessionUpdatePublisher(),
    )
    print("[INFO][BOOT] Runtime stopped cleanly", flush=True)


def start_ws_server_thread(ready_event: threading.Event) -> threading.Thread:
    def run_ws_server():
        asyncio.run(start_server(ready_event=ready_event))

    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()
    return ws_thread


def bootstrap_app(ws_ready_timeout: float = 5.0) -> int:
    print("[INFO][BOOT] Starting SimbioX bootstrap...", flush=True)
    ws_ready_event = threading.Event()
    start_ws_server_thread(ws_ready_event)

    print("[INFO][BOOT] Waiting for WebSocket server...", flush=True)
    if not ws_ready_event.wait(timeout=ws_ready_timeout):
        print(
            "[ERROR][BOOT] WebSocket server did not become ready in time",
            flush=True,
        )
        return 1

    print("[INFO][BOOT] WebSocket server ready", flush=True)
    time.sleep(0.5)

    try:
        main()
    except Exception as exc:
        print(f"[ERROR][BOOT] Fatal runtime error: {exc}", flush=True)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(bootstrap_app())
