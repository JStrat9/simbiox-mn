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

# Zona "de pie": rodilla > KNEE_MAX_ANGLE  →  estado "up"
KNEE_MAX_ANGLE = int(os.getenv("KNEE_MAX_ANGLE", 120))

# Zona de profundidad óptima: PERFECT_DEPTH_MIN ≤ rodilla ≤ PERFECT_DEPTH_MAX  →  estado "down"
PERFECT_DEPTH_MIN = int(os.getenv("PERFECT_DEPTH_MIN", 50))
PERFECT_DEPTH_MAX = int(os.getenv("PERFECT_DEPTH_MAX", 69))

# Error BACK_ROUNDED si ángulo cadera < LEAN_THRESHOLD
LEAN_THRESHOLD = int(os.getenv("LEAN_THRESHOLD", 60))

# Error KNEE_FORWARD si ángulo tobillo-vertical > KNEE_FORWARD_THRESHOLD
KNEE_FORWARD_THRESHOLD = int(os.getenv("KNEE_FORWARD_THRESHOLD", 120))

# Fotogramas consecutivos con un error antes de reportarlo como feedback de rep
ERROR_REPEAT_THRESHOLD = int(os.getenv("ERROR_REPEAT_THRESHOLD", 2))

# Repeticiones confirmadas con el mismo error antes de notificar al entrenador
ERROR_REP_COUNT_THRESHOLD = int(os.getenv("ERROR_REP_COUNT_THRESHOLD", 2))

# KNEE_MIN_ANGLE: reservado para compatibilidad de .env; no activo en lógica del detector.
KNEE_MIN_ANGLE = int(os.getenv("KNEE_MIN_ANGLE", 60))

# -----------------------------------------|
# ---- Parámetros del renegade row     ----|
# -----------------------------------------|

# Brazo abajo (plancha): codo > RENEGADE_ROW_UP_ANGLE  →  estado "down" (ángulo codo alto, brazo extendido)
RENEGADE_ROW_UP_ANGLE = int(os.getenv("RENEGADE_ROW_UP_ANGLE", 140))

# Brazo arriba (tirón completo): codo < RENEGADE_ROW_DOWN_ANGLE  →  estado "up" (ángulo codo bajo, mano cerca cadera)
RENEGADE_ROW_DOWN_ANGLE = int(os.getenv("RENEGADE_ROW_DOWN_ANGLE", 90))

# Error HIP_SAGGING si ángulo cuerpo (hombro-cadera-tobillo) > RENEGADE_ROW_HIP_SAG_THRESHOLD
RENEGADE_ROW_HIP_SAG_THRESHOLD = int(os.getenv("RENEGADE_ROW_HIP_SAG_THRESHOLD", 150))

# Error HIP_HIGH si ángulo cuerpo (hombro-cadera-tobillo) < RENEGADE_ROW_HIP_HIGH_THRESHOLD
RENEGADE_ROW_HIP_HIGH_THRESHOLD = int(os.getenv("RENEGADE_ROW_HIP_HIGH_THRESHOLD", 145))

# ---------------------------------------|
# ---- Parámetros de detección ----|
# ---------------------------------------|
# Umbrales de confianza para MoveNet
POSE_CONFIDENCE_THRESHOLD = float(os.getenv("POSE_CONFIDENCE_THRESHOLD", 0.3))
KEYPOINT_CONFIDENCE_THRESHOLD = float(os.getenv("KEYPOINT_CONFIDENCE_THRESHOLD", 0.3))

# Max number of persons detected by MoveNet
MAX_PERSONS = int(os.getenv("MAX_PERSONS", 6))
