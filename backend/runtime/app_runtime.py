"""
Runtime loop orchestration for camera -> pose -> session pipeline.

PR7 technical debt (explicit):
- This loop has a transitive GUI dependency through `cv2.imshow` and
  `cv2.waitKey` to render/debug and to capture quit input.
- TODO(PR8): decouple canonical runtime flow from GUI event pumping so the
  same loop can run headless without `cv2.waitKey`.
"""

from __future__ import annotations

import os
import time
from queue import Queue

import cv2
import psutil

from communication.websocket_server import emit_session_update
from config import CAMERA_SIDE_URL, MOVENET_TFLITE_MODEL
from detectors.movenet_inference import MoveNet
from detectors.squat_detector_manager import SquatDetectorManager
from runtime.contracts import IdentityResolution
from runtime.process_person import process_person
from session.session_person_manager import SessionPersonManager
from session.session_state import SessionState
from session.session_sync import sync_session_state_for_person
from utils.draw import draw_angles, draw_edges, draw_keypoints
from utils.draw_feedback import draw_feedback
from video.camera_worker import CameraWorker


def run_app_runtime(
    *,
    session_state: SessionState,
    session_manager: SessionPersonManager,
):
    print("[INFO] Cargando MoveNet...")
    movenet = MoveNet(str(MOVENET_TFLITE_MODEL))
    detector_manager = SquatDetectorManager(max_clients=6)

    side_queue = Queue(maxsize=1)
    side_cam = CameraWorker(CAMERA_SIDE_URL, side_queue, name="Side")
    side_cam.start()

    palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]

    process = psutil.Process(os.getpid())
    last_print = time.time()
    frames = 0

    print("[INFO] Iniciando loop principal...")

    class RuntimeIdentityResolver:
        def resolve(self, centroid) -> IdentityResolution:
            client_id, session_person_id = session_manager.resolve_identity(centroid)
            return IdentityResolution(
                client_id=client_id,
                session_person_id=session_person_id,
            )

    identity_resolver = RuntimeIdentityResolver()

    try:
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

            print(f"[TRACK] active clients this frame: {current_client_ids}")
            print("[DEBUG] people detected:", len(people_s))
            session_manager.release_missing_client_ids(current_client_ids)

            cv2.imshow("Side Camera", frame_s)

            frames += 1
            now = time.time()
            if now - last_print >= 1.0:
                fps = frames / (now - last_print)
                cpu = psutil.cpu_percent()
                ram = process.memory_info().rss / 1024 / 1024

                print(f"[PERF][MAIN] fps={fps:.0f} cpu={cpu}% ram={ram:.0f}MB")

                last_print = now
                frames = 0

            # TODO(PR8): remove GUI-bound control flow dependency from canonical runtime.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        side_cam.stop()
        cv2.destroyAllWindows()
