# video/camera_worker.py

import cv2
import threading
import time
from queue import Queue

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

    def start(self):
        """Inicia el hilo de captura."""
        self.running = True
        self.thread.start()

    def stop(self):
        """Detiene el hilo de captura y libera la cámara."""
        self.running = False
        self.thread.join(timeout=1)
        try:
            self.camera.release()
        except Exception:
            pass

    def read(self):
        """Devuelve el último frame disponible o None si no hay."""
        if self.queue.empty():
            return None
        return self.queue.get_nowait()

    def _capture_loop(self):
        """Bucle que lee frames continuamente y los coloca en la cola."""
        while self.running:
            frame = self.camera.read()
            # cv2.VideoCapture.read() returns (ret, frame), while custom wrappers
            # (BaseCamera.read) return the frame or None. Handle both.
            if isinstance(frame, tuple) and len(frame) == 2:
                ret, img = frame
                if not ret:
                    time.sleep(0.01)
                    continue
                frame = img

            if frame is not None:
                if not self.queue.empty():
                    try:
                        self.queue.get_nowait()
                    except Exception:
                        pass
                self.queue.put(frame)
            time.sleep(0.001)  # evita saturar la CPU
