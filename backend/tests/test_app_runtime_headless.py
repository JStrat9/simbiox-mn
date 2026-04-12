import inspect
import sys
import unittest
from pathlib import Path
from queue import Queue

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from runtime import app_runtime
from runtime.app_runtime import run_app_runtime
from runtime.perf_monitor import NullPerfReporter
from runtime.visualization import NullFramePresenter
from domain.session.session_state import SessionState
from interfaces.runtime.session_person_manager_adapter import (
    build_legacy_session_person_manager_adapter,
)


def _fake_person_kp() -> np.ndarray:
    keypoints = np.zeros((17, 3), dtype=float)
    keypoints[:, 2] = 0.9
    keypoints[:, 0] = np.linspace(0.1, 0.9, 17)
    keypoints[:, 1] = np.linspace(0.2, 0.8, 17)
    return keypoints


class _FakeMoveNet:
    def run(self, frame):
        return [_fake_person_kp()]


class _FakeDetector:
    def analyze(self, person_kp):
        return {"valid": True, "reps": 1, "errors": [], "angles": {}}


class _FakeDetectorManager:
    def get(self, session_person_id: str):
        return _FakeDetector()


class _FakeCamera:
    def __init__(self, queue: Queue):
        self.queue = queue
        self.stopped = False

    def start(self):
        if self.queue.empty():
            self.queue.put(np.zeros((16, 16, 3), dtype=np.uint8))

    def stop(self):
        self.stopped = True


class _NoFrameCamera:
    def __init__(self):
        self.stopped = False

    def start(self):
        return True

    def stop(self):
        self.stopped = True

    def status(self):
        return {
            "start_attempted": True,
            "camera_opened": True,
            "first_frame_received": False,
            "consecutive_read_failures": 100,
            "degraded_reason": "camera_no_frames",
        }


class _PresenterSpy(NullFramePresenter):
    def __init__(self):
        self.present_calls = 0
        self.closed = False

    def present(self, frame):
        self.present_calls += 1

    def close(self):
        self.closed = True


class _StopAfterFirstPresentedFrame:
    def __init__(self, presenter: _PresenterSpy):
        self.presenter = presenter

    def should_stop(self) -> bool:
        return self.presenter.present_calls >= 1


class _PerfSpy(NullPerfReporter):
    def __init__(self):
        self.ticks = 0

    def tick(self):
        self.ticks += 1


class _SessionUpdatePublisherSpy:
    def __init__(self):
        self.publish_calls = 0

    def publish(self):
        self.publish_calls += 1


class AppRuntimeHeadlessTests(unittest.TestCase):
    def test_headless_runtime_runs_without_gui_and_updates_state(self):
        state = SessionState()
        manager = build_legacy_session_person_manager_adapter(
            session_state=state,
            max_persons=6,
            distance_threshold=120.0,
        )

        side_queue = Queue(maxsize=1)
        fake_camera = _FakeCamera(side_queue)
        presenter = _PresenterSpy()
        control = _StopAfterFirstPresentedFrame(presenter)
        perf = _PerfSpy()

        run_app_runtime(
            session_state=state,
            session_manager=manager,
            frame_presenter=presenter,
            runtime_control=control,
            perf_reporter=perf,
            side_queue=side_queue,
            side_camera=fake_camera,
            movenet=_FakeMoveNet(),
            detector_manager=_FakeDetectorManager(),
        )

        self.assertTrue(fake_camera.stopped)
        self.assertTrue(presenter.closed)
        self.assertGreaterEqual(presenter.present_calls, 1)
        self.assertGreaterEqual(perf.ticks, 1)
        self.assertEqual(state.reps["athlete_1"], 1)
        self.assertGreaterEqual(state.version, 1)

    def test_headless_runtime_uses_injected_session_update_publisher(self):
        state = SessionState()
        manager = build_legacy_session_person_manager_adapter(
            session_state=state,
            max_persons=6,
            distance_threshold=120.0,
        )

        side_queue = Queue(maxsize=1)
        fake_camera = _FakeCamera(side_queue)
        presenter = _PresenterSpy()
        control = _StopAfterFirstPresentedFrame(presenter)
        perf = _PerfSpy()
        publisher = _SessionUpdatePublisherSpy()

        run_app_runtime(
            session_state=state,
            session_manager=manager,
            frame_presenter=presenter,
            runtime_control=control,
            perf_reporter=perf,
            side_queue=side_queue,
            side_camera=fake_camera,
            movenet=_FakeMoveNet(),
            detector_manager=_FakeDetectorManager(),
            session_update_publisher=publisher,
        )

        self.assertEqual(publisher.publish_calls, 1)

    def test_runtime_fails_cleanly_when_camera_never_produces_initial_frame(self):
        state = SessionState()
        manager = build_legacy_session_person_manager_adapter(
            session_state=state,
            max_persons=6,
            distance_threshold=120.0,
        )

        side_queue = Queue(maxsize=1)
        no_frame_camera = _NoFrameCamera()
        presenter = _PresenterSpy()
        perf = _PerfSpy()

        with self.assertRaisesRegex(
            RuntimeError,
            "Camera startup failed: camera_no_frames",
        ):
            run_app_runtime(
                session_state=state,
                session_manager=manager,
                frame_presenter=presenter,
                perf_reporter=perf,
                side_queue=side_queue,
                side_camera=no_frame_camera,
                movenet=_FakeMoveNet(),
                detector_manager=_FakeDetectorManager(),
                initial_frame_timeout_s=0.01,
            )

        self.assertTrue(no_frame_camera.stopped)
        self.assertTrue(presenter.closed)

    def test_canonical_loop_has_no_direct_waitkey_dependency(self):
        source = inspect.getsource(app_runtime.run_app_runtime)
        self.assertNotIn("cv2.waitKey", source)

    def test_runtime_module_has_no_direct_ws_transport_dependency(self):
        source = inspect.getsource(app_runtime)
        self.assertNotIn("communication.websocket_server", source)

    def test_runtime_module_has_no_direct_legacy_session_manager_dependency(self):
        source = inspect.getsource(app_runtime)
        self.assertNotIn("session.session_person_manager", source)


if __name__ == "__main__":
    unittest.main()
