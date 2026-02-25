"""Runtime loop orchestration for camera -> pose -> session pipeline.

PR8 debt closure:
- Canonical runtime loop no longer depends directly on OpenCV GUI calls.
- GUI control/rendering is injected through runtime adapters.
"""

from __future__ import annotations

import time
from queue import Queue
from typing import Any, Protocol

from application.ports.session_update_publisher import (
    NullSessionUpdatePublisher,
    SessionUpdatePublisher,
)
from application.ports.process_person_ports import IdentityResolution
from application.use_cases.process_person_uc import process_person
from domain.session.session_state import SessionState
from domain.session.sync_policy import sync_session_state_for_person
from runtime.perf_monitor import NullPerfReporter, PerfReporter
from runtime.visualization import (
    HeadlessRuntimeControl,
    NullFramePresenter,
    FramePresenter,
    RuntimeControl,
)
from session.session_person_manager import SessionPersonManager
from utils.draw import draw_angles, draw_edges, draw_keypoints
from utils.draw_feedback import draw_feedback


class CameraPort(Protocol):
    def start(self):
        ...

    def stop(self):
        ...


def run_app_runtime(
    *,
    session_state: SessionState,
    session_manager: SessionPersonManager,
    frame_presenter: FramePresenter | None = None,
    runtime_control: RuntimeControl | None = None,
    perf_reporter: PerfReporter | None = None,
    side_queue: Queue | None = None,
    side_camera: CameraPort | None = None,
    movenet: Any | None = None,
    detector_manager: Any | None = None,
    session_update_publisher: SessionUpdatePublisher | None = None,
):
    if frame_presenter is None:
        frame_presenter = NullFramePresenter()
    if runtime_control is None:
        runtime_control = HeadlessRuntimeControl()
    if perf_reporter is None:
        perf_reporter = NullPerfReporter()
    if session_update_publisher is None:
        session_update_publisher = NullSessionUpdatePublisher()
    if side_queue is None:
        side_queue = Queue(maxsize=1)
    if movenet is None:
        from config import MOVENET_TFLITE_MODEL
        from detectors.movenet_inference import MoveNet

        print("[INFO] Cargando MoveNet...")
        movenet = MoveNet(str(MOVENET_TFLITE_MODEL))
    if detector_manager is None:
        from detectors.squat_detector_manager import SquatDetectorManager

        detector_manager = SquatDetectorManager(max_clients=6)
    if side_camera is None:
        from config import CAMERA_SIDE_URL
        from video.camera_worker import CameraWorker

        side_camera = CameraWorker(CAMERA_SIDE_URL, side_queue, name="Side")
    side_camera.start()

    palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]

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
            if runtime_control.should_stop():
                break

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
                session_update_publisher.publish()

            print(f"[TRACK] active clients this frame: {current_client_ids}")
            print("[DEBUG] people detected:", len(people_s))
            session_manager.release_missing_client_ids(current_client_ids)

            frame_presenter.present(frame_s)
            perf_reporter.tick()
    finally:
        side_camera.stop()
        frame_presenter.close()
