import os
from dotenv import load_dotenv

load_dotenv()

# Camera URLs
CAMERA_FRONT_URL = os.getenv("CAMERA_FRONT_URL")
CAMERA_SIDE_URL = os.getenv("CAMERA_SIDE_URL")

# Model MoveNet TGLite
MOVENET_TFLITE_MODEL = os.getenv("MOVENET_TFLITE_MODEL")

# ---------------------------------------|
# ---- Parámetros de la sentadilla ----|
# ---------------------------------------|
# Umbrales de ángulos
KNEE_MIN_ANGLE = int(os.getenv("KNEE_MIN_ANGLE", 60))
KNEE_MAX_ANGLE = int(os.getenv("KNEE_MAX_ANGLE", 120))

# Ángulos ideales sentadilla profunda
PERFECT_DEPTH_MIN = int(os.getenv("PERFECT_DEPTH_MIN", 50))
PERFECT_DEPTH_MAX = int(os.getenv("PERFECT_DEPTH_MAX", 69))

# Parámetros de forma
LEAN_THRESHOLD = int(os.getenv("LEAN_THRESHOLD", 60))
KNEE_FORWARD_THRESHOLD = int(os.getenv("KNEE_FORWARD_THRESHOLD", 120))

# ---------------------------------------|
# ---- Parámetros de detección ----|
# ---------------------------------------|
# Umbrales de confianza para MoveNet
POSE_CONFIDENCE_THRESHOLD = float(os.getenv("POSE_CONFIDENCE_THRESHOLD", 0.3))  # Umbral para score de pose
KEYPOINT_CONFIDENCE_THRESHOLD = float(os.getenv("KEYPOINT_CONFIDENCE_THRESHOLD", 0.3))  # Umbral promedio de keypoints

# Umbral de repeticiones de error para enviar feedback
ERROR_REPEAT_THRESHOLD = int(os.getenv("ERROR_REPEAT_THRESHOLD", 2))

