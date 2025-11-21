# camera_side.py
from .base_camera import BaseCamera

DEFAULT_SIDE_RTSP = "rtsp://admin:JLD@SimbioxMVP4928@192.168.1.17:554/h264Preview_01_sub"

class SideCamera(BaseCamera):
    def __init__(self, source: str = DEFAULT_SIDE_RTSP, use_ffmpeg: bool = True):
        super().__init__(source=source, use_ffmpeg=use_ffmpeg, name="camera_side")