# backend/main.py

import asyncio
import threading

from config import CAMERAS
from websocket.websocket_server import start_server
from video.camera_worker import start_camera_worker