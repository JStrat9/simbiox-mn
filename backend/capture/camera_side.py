# camera_side.py
from .base_camera import BaseCamera
from config import CAMERA_SIDE_URL

class SideCamera(BaseCamera):
    def __init__(self, source: str = CAMERA_SIDE_URL, use_ffmpeg: bool = True):
        super().__init__(source=source, use_ffmpeg=use_ffmpeg, name="camera_side")