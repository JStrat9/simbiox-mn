import threading
import time
import queue
import cv2


class FrameGrabber:
    """
    Captures frames from a video source in a separate thread and only returns the latest frame. Ideal for RTSP streams.
    - frame_queue: queue.Queue(maxsize=1)
    - max_fps: controls the maximum frame rate for capturing frames (None means no limit)
    """

    def __init__(self,  cap: cv2.VideoCapture, frame_queue: queue.Queue, max_fps: float = None):
        self.cap = cap
        self.frame_queue = frame_queue
        self.max_fps = max_fps

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.is_running = False
        self.last_timestamp = None

    def start(self):
        self.is_running = True
        self.thread.start()
    
    def stop(self):
        self.is_running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _run(self):
        delay = 1.0 / self.max_fps if self.max_fps else 0

        while self.is_running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.05)
                continue

            # Copy the frame to avoid shared refernces issues.
            frame = frame.copy()

            # If the queue is full, remove the existing frame.
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                try:
                    self.frame_queue.get_nowait() # Remove the old frame
                except queue.Empty:
                    pass
                self.frame_queue.put_nowait(frame)

            self.last_timestamp = time.time()

            if delay > 0:
                time.sleep(delay)


