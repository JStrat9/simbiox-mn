# bas_camera.py
import cv2
from typing import Optional, Tuple

class BaseCamera:
    """Base class for camera capture. Encapsulates cv2.VideoCapture and provides simple methods to open, read, and release the camera."""

    def __init__(self, source: str, use_ffmpeg: bool = False, name: str = "camera"):
        """source: URL RTSP or path to video file.
        use_ffmpeg: if True, use FFMPEG (better for RTSP in many systems)"""
        self.source = source
        self.use_ffmpeg = use_ffmpeg
        self.name = name
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        """Open the source for capturing. Returns True if successful."""
        if self.cap is not None and self.cap.isOpened():
            return True
        
        try:
            if self.use_ffmpeg:
                # many OpenCV builds builds recognize cv.CAP_FFMPEG
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            else:
                self.cap = cv2.VideoCapture(self.source)
        except Exception as e:
            print(f"[{self.name}] Error opening VideoCapture: {e}")
            self.cap = None
            return False
        
        opened = self.cap.isOpened()
        if not opened:
            print(f"[{self.name}] Failed to open source: {self.source}")
            # Release cap if failed to open
            try:
                if self.cap:
                    self.cap.release()
            except Exception:
                pass
            self.cap = None
        else:
            print(f"[{self.name}] Successfully opened source: {self.source}")

        return opened
    
    def read(self):
        """Read a frame from the capture. Returns the frame or None if failed."""
        if self.cap is None or not self.cap.isOpened():
            self.open()

        if self.cap is None or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                return None
            return frame
        except Exception as e:
            print(f"[{self.name}] Error reading frame: {e}")
            return None
        
    def release(self):
        """Releas the capture"""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                print(f"[{self.name}] Error releasing VideoCapture: {e}")
            self.cap = None
    
    def is_opened(self) -> bool:
        """Returns True if the capture is opened."""
        return self.cap is not None and self.cap.isOpened()