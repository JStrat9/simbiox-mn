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
    run_app_runtime(
        session_state=session_state,
        session_manager=session_manager,
        frame_presenter=OpenCVFramePresenter(window_name="Side Camera"),
        runtime_control=OpenCVKeypressControl(quit_key="q", wait_ms=1),
        perf_reporter=PsutilPerfReporter(label="MAIN"),
        session_update_publisher=WebSocketSessionUpdatePublisher(),
    )


if __name__ == "__main__":
    ws_ready_event = threading.Event()

    def run_ws_server():
        asyncio.run(start_server(ready_event=ws_ready_event))

    # WebSocket server thread
    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()

    # Esperar a que el servidor WebSocket esté listo
    print("[INFO] Esperando a que el servidor WebSocket esté listo...")
    ws_ready_event.wait(timeout=5.0)
    print("[INFO] Servidor WebSocket listo!")

    # Pequeña pausa adicional para asegurar que todo está inicializado
    time.sleep(0.5)

    main()
