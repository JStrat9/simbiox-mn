#camera_front.py
from .base_camera import BaseCamera
from config import CAMERA_FRONT_URL

class FrontCamera(BaseCamera):
    def __init__(self, source: str = CAMERA_FRONT_URL, use_ffmpeg: bool = True):
        super().__init__(source=source, use_ffmpeg=use_ffmpeg, name="camera_front")
