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
from application.ports.session_person_manager_ports import RuntimeSessionManagerPort
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
from utils.draw import draw_angles, draw_edges, draw_keypoints
from utils.draw_feedback import draw_feedback


class CameraPort(Protocol):
    def start(self):
        ...

    def stop(self):
        ...


def _camera_status(camera: CameraPort | None) -> dict[str, Any]:
    if camera is None:
        return {}

    status_fn = getattr(camera, "status", None)
    if callable(status_fn):
        try:
            status = status_fn()
            if isinstance(status, dict):
                return status
        except Exception:
            return {}
    return {}


def _wait_for_initial_frame(
    *,
    side_queue: Queue,
    side_camera: CameraPort,
    timeout_s: float,
) -> None:
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        if not side_queue.empty():
            print("[INFO][RUNTIME] First frame received", flush=True)
            return

        status = _camera_status(side_camera)
        degraded_reason = status.get("degraded_reason")
        if degraded_reason == "camera_not_open":
            raise RuntimeError("Camera startup failed: camera_not_open")

        time.sleep(0.01)

    status = _camera_status(side_camera)
    degraded_reason = status.get("degraded_reason") or "no_initial_frame"
    raise RuntimeError(f"Camera startup failed: {degraded_reason}")


def _process_camera_frame(
    *,
    queue: Queue,
    movenet: Any,
    session_state: SessionState,
    resolver: Any,
    detector_manager: Any,
    frame_presenter: FramePresenter | None,
) -> bool:
    """
    Pull one frame from queue, run MoveNet, draw overlays, present, and
    process only the most prominent person (people[0]).
    Returns True if session state changed.
    """
    if queue.empty():
        return False

    frame_data = queue.get()
    people = movenet.run(frame_data)

    state_changed = False

    if people:
        # Pilot mode: process only the most prominent detection.
        person_kp = people[0]

        output = process_person(
            person_kp,
            session_state=session_state,
            identity_resolver=resolver,
            station_provider=resolver,
            detector_provider=detector_manager,
            sync_state_fn=sync_session_state_for_person,
            on_squat_feedback=None,
        )

        if not output.skipped:
            draw_edges(frame_data, person_kp)
            draw_keypoints(frame_data, person_kp)
            angles = output.result.get("angles") or {}
            if angles:
                draw_angles(frame_data, person_kp, angles, output.side)
            draw_feedback(
                frame_data,
                reps=output.result.get("reps"),
                error=output.result.get("feedback") or None,
            )

            print(
                f"[EXERCISE] {output.session_person_id} "
                f"station={output.station.station_id} "
                f"exercise={output.station.exercise} "
                f"reps={output.station.reps}"
            )

            resolver.release_missing_client_ids(
                {output.client_id} if output.client_id else set()
            )

            state_changed = output.state_changed

    # Present frame (raw if no detection, annotated if detection found).
    if frame_presenter is not None:
        frame_presenter.present(frame_data)

    return state_changed


def run_app_runtime(
    *,
    session_state: SessionState,
    session_manager: RuntimeSessionManagerPort,
    frame_presenter: FramePresenter | None = None,
    runtime_control: RuntimeControl | None = None,
    perf_reporter: PerfReporter | None = None,
    side_queue: Queue | None = None,
    side_camera: CameraPort | None = None,
    front_queue: Queue | None = None,
    front_camera: CameraPort | None = None,
    front_session_manager: Any | None = None,
    front_frame_presenter: FramePresenter | None = None,
    movenet: Any | None = None,
    detector_manager: Any | None = None,
    session_update_publisher: SessionUpdatePublisher | None = None,
    initial_frame_timeout_s: float = 3.0,
):
    if frame_presenter is None:
        frame_presenter = NullFramePresenter()
    if front_frame_presenter is None:
        front_frame_presenter = NullFramePresenter()
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
        from detectors.exercise_detector_router import ExerciseDetectorRouter

        detector_manager = ExerciseDetectorRouter(max_clients=6)
    if side_camera is None:
        from config import CAMERA_SIDE_URL
        from video.camera_worker import CameraWorker

        side_camera = CameraWorker(CAMERA_SIDE_URL, side_queue, name="Side")

    # Dual-camera mode: activate when front_camera is provided.
    dual_camera = front_camera is not None
    if dual_camera:
        if front_queue is None:
            front_queue = Queue(maxsize=1)
        if front_session_manager is None:
            from interfaces.runtime.static_camera_adapter import StaticCameraSessionAdapter
            front_session_manager = StaticCameraSessionAdapter("athlete_2", session_state)

    # In dual-camera mode use static adapters for both cameras to prevent
    # cross-camera tracker ID collisions (both feeds share normalized coords).
    # In single-camera mode the legacy session_manager (IoU tracker) is used.
    if dual_camera:
        from interfaces.runtime.static_camera_adapter import StaticCameraSessionAdapter
        side_resolver: Any = StaticCameraSessionAdapter("athlete_1", session_state)
    else:
        side_resolver = session_manager

    print("[INFO][RUNTIME] Starting runtime loop...", flush=True)

    try:
        side_camera.start()
        _wait_for_initial_frame(
            side_queue=side_queue,
            side_camera=side_camera,
            timeout_s=initial_frame_timeout_s,
        )

        if dual_camera:
            front_camera.start()
            try:
                _wait_for_initial_frame(
                    side_queue=front_queue,
                    side_camera=front_camera,
                    timeout_s=initial_frame_timeout_s,
                )
            except RuntimeError as exc:
                print(
                    f"[WARN][RUNTIME] Front camera failed to start: {exc}. "
                    "Falling back to single-camera mode.",
                    flush=True,
                )
                front_camera.stop()
                dual_camera = False
                front_camera = None

        while True:
            if runtime_control.should_stop():
                break

            frame_state_changed = False

            # --- Side camera ---
            if not side_queue.empty():
                changed = _process_camera_frame(
                    queue=side_queue,
                    movenet=movenet,
                    session_state=session_state,
                    resolver=side_resolver,
                    detector_manager=detector_manager,
                    frame_presenter=frame_presenter,
                )
                frame_state_changed = frame_state_changed or changed

            # --- Front camera (only in dual-camera mode) ---
            if dual_camera and not front_queue.empty():
                changed = _process_camera_frame(
                    queue=front_queue,
                    movenet=movenet,
                    session_state=session_state,
                    resolver=front_session_manager,
                    detector_manager=detector_manager,
                    frame_presenter=front_frame_presenter,
                )
                frame_state_changed = frame_state_changed or changed

            if frame_state_changed:
                session_update_publisher.publish()

            both_empty = side_queue.empty() and (
                not dual_camera or front_queue.empty()
            )
            if both_empty:
                time.sleep(0.001)

            perf_reporter.tick()

    except Exception as exc:
        print(f"[ERROR][RUNTIME] Fatal runtime exception: {exc}", flush=True)
        raise
    finally:
        print("[INFO][RUNTIME] Shutting down runtime...", flush=True)
        side_camera.stop()
        if dual_camera and front_camera is not None:
            front_camera.stop()
        frame_presenter.close()
        front_frame_presenter.close()
