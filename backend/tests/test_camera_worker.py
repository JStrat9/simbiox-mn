import sys
import unittest
from pathlib import Path
from queue import Queue

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from video.camera_worker import CameraWorker


class _ClosedCamera:
    def isOpened(self):
        return False

    def release(self):
        return None


class _ExceptionCamera:
    def isOpened(self):
        return True

    def read(self):
        raise RuntimeError("boom")

    def release(self):
        return None


class CameraWorkerTests(unittest.TestCase):
    def test_start_reports_camera_not_open(self):
        worker = CameraWorker(_ClosedCamera(), Queue(maxsize=1), name="TestCam")

        started = worker.start()

        self.assertFalse(started)
        self.assertEqual(worker.status()["degraded_reason"], "camera_not_open")

    def test_capture_loop_marks_read_exception_as_degraded(self):
        worker = CameraWorker(_ExceptionCamera(), Queue(maxsize=1), name="TestCam")

        worker.start()
        worker.thread.join(timeout=0.05)
        worker.stop()

        self.assertEqual(worker.status()["degraded_reason"], "camera_read_exception")


if __name__ == "__main__":
    unittest.main()
