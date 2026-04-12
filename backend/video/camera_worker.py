# video/camera_worker.py

import cv2
import threading
import time
from queue import Queue

_MAX_STARTUP_READ_FAILURES = 30


class CameraWorker:
    """
    Worker para capturar frames de una cámara en un hilo separado
    y enviarlos a una Queue para procesamiento.
    """

    def __init__(self, camera, frame_queue=None, name="camera"):
        """
        camera: puede ser una instancia con método read()/release() (p.ej. FrontCamera)
                o una URL/string que será pasada a `cv2.VideoCapture`.
        frame_queue: instancia de `queue.Queue` donde se colocarán los frames.
                     Si es None, se crea una cola interna con tamaño 1.
        name: nombre descriptivo para debug/logs
        """
        # Si camera es una cadena, interpretarla como source para VideoCapture
        if isinstance(camera, str):
            self.camera = cv2.VideoCapture(camera)
        else:
            self.camera = camera

        self.name = name
        # usar la Queue proporcionada por el caller si existe
        self.queue = frame_queue if frame_queue is not None else Queue(maxsize=1)
        self.running = False
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.start_attempted = False
        self.camera_opened: bool | None = None
        self.first_frame_received = False
        self.consecutive_read_failures = 0
        self.degraded_reason: str | None = None

    def start(self):
        """Inicia el hilo de captura."""
        self.start_attempted = True
        if hasattr(self.camera, "isOpened"):
            try:
                self.camera_opened = bool(self.camera.isOpened())
            except Exception:
                self.camera_opened = None
            if self.camera_opened is False:
                self.degraded_reason = "camera_not_open"
                print(
                    f"[ERROR][CAMERA][{self.name}] Camera source could not be opened",
                    flush=True,
                )
                return False

        self.running = True
        self.thread.start()
        print(f"[INFO][CAMERA][{self.name}] Capture thread started", flush=True)
        return True

    def stop(self):
        """Detiene el hilo de captura y libera la cámara."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1)
        try:
            self.camera.release()
        except Exception:
            pass
        print(f"[INFO][CAMERA][{self.name}] Capture thread stopped", flush=True)

    def read(self):
        """Devuelve el último frame disponible o None si no hay."""
        if self.queue.empty():
            return None
        return self.queue.get_nowait()

    def status(self):
        return {
            "start_attempted": self.start_attempted,
            "camera_opened": self.camera_opened,
            "first_frame_received": self.first_frame_received,
            "consecutive_read_failures": self.consecutive_read_failures,
            "degraded_reason": self.degraded_reason,
        }

    def _capture_loop(self):
        """Bucle que lee frames continuamente y los coloca en la cola."""
        while self.running:
            try:
                frame = self.camera.read()
            except Exception as exc:
                self.consecutive_read_failures += 1
                if self.degraded_reason != "camera_read_exception":
                    self.degraded_reason = "camera_read_exception"
                    print(
                        f"[ERROR][CAMERA][{self.name}] Camera read raised exception: {exc}",
                        flush=True,
                    )
                time.sleep(0.01)
                continue

            # cv2.VideoCapture.read() returns (ret, frame), while custom wrappers
            # (BaseCamera.read) return the frame or None. Handle both.
            if isinstance(frame, tuple) and len(frame) == 2:
                ret, img = frame
                if not ret:
                    self.consecutive_read_failures += 1
                    if self.consecutive_read_failures >= _MAX_STARTUP_READ_FAILURES:
                        self.degraded_reason = "camera_read_failed"
                    time.sleep(0.01)
                    continue
                frame = img

            if frame is not None:
                self.consecutive_read_failures = 0
                self.first_frame_received = True
                self.degraded_reason = None
                if not self.queue.empty():
                    try:
                        self.queue.get_nowait()
                    except Exception:
                        pass
                self.queue.put(frame)
            else:
                self.consecutive_read_failures += 1
                if self.consecutive_read_failures >= _MAX_STARTUP_READ_FAILURES:
                    self.degraded_reason = "camera_no_frames"
            time.sleep(0.001)  # evita saturar la CPU
