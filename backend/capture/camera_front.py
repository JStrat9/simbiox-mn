#camera_front.py
from .base_camera import BaseCamera

DEFAULT_FRONT_RTSP = "rtsp://admin:JLD@SimbioxMVP4928-2@192.168.1.23:554/h264Preview_01_sub"

class FrontCamera(BaseCamera):
    def __init__(self, source: str = DEFAULT_FRONT_RTSP, use_ffmpeg: bool = True):
        super().__init__(source=source, use_ffmpeg=use_ffmpeg, name="camera_front")
