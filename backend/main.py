# main.py

# TODO CONTINUAR CON CHATGPT "Verificación manual que debes hacer ahora"
# Rotar estación sin persona en cámara
# Rotar estación mientras se ejecuta squat
# Rotar ida y vuelta (A -> B -> A)

import asyncio
import cv2
from queue import Queue
import time
import os
import psutil
import threading

from video.camera_worker import CameraWorker
from detectors.movenet_inference import MoveNet
from detectors.squat_detector_manager import SquatDetectorManager
from utils.draw import draw_keypoints, draw_edges, draw_angles
from utils.draw_feedback import draw_feedback
from communication.websocket_server import (
    emit_session_update,
    start_server,
    register_rotate_station_handler,
    register_session_state,
)
from tracking.tracker_iou import CentroidTracker

from runtime.contracts import IdentityResolution
from runtime.process_person import process_person
from session.session_state import SessionState
from session.session_person_manager import SessionPersonManager
from session.session_sync import sync_session_state_for_person
from config import (
    MAX_PERSONS,
    CAMERA_SIDE_URL,
    MOVENET_TFLITE_MODEL,
)

session_state = SessionState()
session_manager = SessionPersonManager(
    max_persons=MAX_PERSONS,
    t_active=0.8,
    t_lost=2.0,
    distance_threshold=120.0,
)
session_manager.session_state = session_state
register_session_state(session_state)


def on_rotate_station(session_person_id: str, station_id: str):
    session_manager.assign_station(session_person_id, station_id)
    session_state.set_assignment(session_person_id, station_id)

    print(
        f"[SESSION][ROTATION] "
        f"{session_person_id} -> {station_id}",
        flush=True,
    )


register_rotate_station_handler(on_rotate_station)


def main():
    # Inicializar MoveNet
    print("[INFO] Cargando MoveNet...")
    movenet = MoveNet(str(MOVENET_TFLITE_MODEL))

    detector_manager = SquatDetectorManager(max_clients=6)

    # Inicializar camara con CameraWorker
    side_queue = Queue(maxsize=1)
    side_cam = CameraWorker(CAMERA_SIDE_URL, side_queue, name="Side")

    side_cam.start()

    palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]

    # Variables de performance
    process = psutil.Process(os.getpid())
    last_print = time.time()
    frames = 0

    print("[INFO] Iniciando loop principal...")

    tracker = CentroidTracker(max_clients=6, distance_threshold=100)

    class RuntimeIdentityResolver:
        def resolve(self, centroid) -> IdentityResolution:
            client_id = tracker.get_client_id(centroid)
            session_person_id = session_manager.resolve_person(client_id, centroid)
            return IdentityResolution(
                client_id=client_id,
                session_person_id=session_person_id,
            )

    identity_resolver = RuntimeIdentityResolver()

    while True:
        if side_queue.empty():
            time.sleep(0.001)
            continue

        current_client_ids = set()

        frame_s = side_queue.get()
        people_s = movenet.run(frame_s)

        frame_state_changed = False

        for idx, person_kp in enumerate(people_s):
            def render_squat_feedback(*, person_kp, side, result):
                draw_feedback(
                    frame_s,
                    reps=result.get("reps"),
                    error=result["errors"][0] if result.get("errors") else "",
                )
                draw_keypoints(frame_s, person_kp, color=palette[idx % len(palette)])
                draw_edges(frame_s, person_kp)
                draw_angles(frame_s, person_kp, result.get("angles", {}), side)

            output = process_person(
                person_kp,
                session_state=session_state,
                identity_resolver=identity_resolver,
                station_provider=session_manager,
                detector_provider=detector_manager,
                sync_state_fn=sync_session_state_for_person,
                on_squat_feedback=render_squat_feedback,
            )

            if output.skipped:
                # If there are no available IDs, skip this person
                continue

            current_client_ids.add(output.client_id)

            print(
                f"[EXERCISE] {output.session_person_id} "
                f"station={output.station.station_id} "
                f"exercise={output.station.exercise} "
                f"reps={output.station.reps}"
            )
            if output.is_squat_station:
                print(
                    f"[SESSION] client_id={output.client_id} "
                    f"-> session_person_id={output.session_person_id}"
                )

            frame_state_changed = frame_state_changed or output.state_changed

            print(
                f"[SIDE] Persona {idx}: "
                f"lado={output.side}, resultado={output.result}"
            )

        if frame_state_changed:
            emit_session_update()

        # --- Release missing clients ---
        print(f"[TRACK] active clients this frame: {current_client_ids}")
        print("[DEBUG] people detected:", len(people_s))
        tracker.release_missing(current_client_ids)

        cv2.imshow("Side Camera", frame_s)

        # --- Performance (FPS / CPU / RAM) ---
        frames += 1
        now = time.time()
        if now - last_print >= 1.0:
            fps = frames / (now - last_print)
            cpu = psutil.cpu_percent()
            ram = process.memory_info().rss / 1024 / 1024

            print(f"[PERF][MAIN] fps={fps:.0f} cpu={cpu}% ram={ram:.0f}MB")

            last_print = now
            frames = 0

        # --- Salida ---
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    side_cam.stop()
    cv2.destroyAllWindows()


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
