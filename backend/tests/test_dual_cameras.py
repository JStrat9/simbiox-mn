# tests/test_dual_cameras.py
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture.camera_front import FrontCamera
from capture.camera_side import SideCamera
from utils.performance import PerformanceLogger

import cv2
import tensorflow as tf
import numpy as np
import time
import threading
from queue import Queue

# -----------------------
# Configuración MoveNet
# -----------------------
MODEL_PATH = str(Path(__file__).resolve().parent.parent.joinpath("movenet_multipose.tflite"))
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"MoveNet TFLite model not found at: {MODEL_PATH}")

print("[INFO] Cargando MoveNet MultiPose (TFLite)...")
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Derive input size and dtype from TFLite model
tflite_input_shape = input_details[0]['shape']  # [1, height, width, 3]
TFLITE_INPUT_H = int(tflite_input_shape[1])
TFLITE_INPUT_W = int(tflite_input_shape[2])
TFLITE_INPUT_DTYPE = input_details[0]['dtype']

print(f"[INFO] MoveNet TFLite loaded: input={TFLITE_INPUT_W}x{TFLITE_INPUT_H}, dtype={TFLITE_INPUT_DTYPE}")

KEYPOINT_EDGES = {
    (0,1), (0,2), (1,3), (2,4),
    (0,5), (0,6), (5,7), (7,9),
    (6,8), (8,10), (5,6), (5,11),
    (6,12), (11,12), (11,13), (13,15),
    (12,14), (14,16)
}

# -----------------------
# Funciones de detección y dibujo
# -----------------------
def detect_pose(frame):
    """Detect pose using TFLite interpreter.
    
    Args:
        frame: Input frame (BGR from OpenCV or RGB)
    
    Returns:
        List of keypoints arrays, each shape (17, 3) for [y, x, confidence]
    """
    # Resize to model input size
    img_resized = cv2.resize(frame, (TFLITE_INPUT_W, TFLITE_INPUT_H))

    # Prepare input tensor with correct dtype
    if TFLITE_INPUT_DTYPE == np.uint8:
        input_tensor = np.expand_dims(img_resized.astype(np.uint8), axis=0)
    else:
        # Fallback to float32 normalized [0,1]
        input_tensor = np.expand_dims(img_resized.astype(np.float32) / 255.0, axis=0)

    # Run inference
    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()
    outputs = interpreter.get_tensor(output_details[0]['index'])  # [1, num_people, 56]
    outputs = np.copy(outputs)

    people = []
    kp_raw = outputs  # [1, N, 56]
    for person_raw in kp_raw[0]:
        # First 51 elements are 17 keypoints * 3 (y, x, confidence)
        keypoints = person_raw[:51].reshape((17, 3))
        score = person_raw[55]
        if score > 0.1:
            people.append(keypoints)
    return people

def draw_keypoints(frame, keypoints, color=(0,255,0), threshold=0.3):
    h, w, _ = frame.shape
    for y, x, c in keypoints:
        if c > threshold:
            cv2.circle(frame, (int(x*w), int(y*h)), 4, color, -1)

def draw_edges(frame, keypoints, color=(255,255,255), threshold=0.3):
    h, w, _ = frame.shape
    for i, j in KEYPOINT_EDGES:
        y1, x1, c1 = keypoints[i]
        y2, x2, c2 = keypoints[j]
        if c1 > threshold and c2 > threshold:
            cv2.line(frame, (int(x1*w), int(y1*h)), (int(x2*w), int(y2*h)), color, 2)

# -----------------------
# Inicializar cámaras y logger
# -----------------------
cam_front = FrontCamera()
cam_side = SideCamera()

perf_logger = PerformanceLogger()
palette = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]

queue_front_frames = Queue(maxsize=1)
queue_side_frames  = Queue(maxsize=1)
queue_front_results = Queue(maxsize=1)
queue_side_results  = Queue(maxsize=1)

# -----------------------
# Hilos de captura
# -----------------------
def capture_thread(cam, frame_queue, name):
    while True:
        frame = cam.read()
        if frame is not None:
            if not frame_queue.empty():
                try: frame_queue.get_nowait()
                except: pass
            frame_queue.put(frame)
        time.sleep(0.001)

# -----------------------
# Hilos de inferencia
# -----------------------
def inference_thread(frame_queue, result_queue, name):
    while True:
        if frame_queue.empty():
            time.sleep(0.001)
            continue
        frame = frame_queue.get()
        t0 = time.time()
        try:
            people = detect_pose(frame)
        except Exception as e:
            print(f"[ERROR] {name} inference: {e}")
            continue

        latency = (time.time() - t0) * 1000

        if not result_queue.empty():
            try: result_queue.get_nowait()
            except: pass
        result_queue.put((frame, people, latency))
        perf_logger.log_frame(name, latency)

# -----------------------
# Lanzar hilos
# -----------------------
threading.Thread(target=capture_thread, args=(cam_front, queue_front_frames, "front"), daemon=True).start()
threading.Thread(target=capture_thread, args=(cam_side, queue_side_frames, "side"), daemon=True).start()
threading.Thread(target=inference_thread, args=(queue_front_frames, queue_front_results, "front"), daemon=True).start()
threading.Thread(target=inference_thread, args=(queue_side_frames, queue_side_results, "side"), daemon=True).start()

# -----------------------
# Loop principal: visualización
# -----------------------
print("[INFO] Iniciando visualización de cámaras...")
while True:
    if not queue_front_results.empty():
        frame_f, people_f, latency_f = queue_front_results.get()
        for idx, kp in enumerate(people_f):
            draw_keypoints(frame_f, kp, color=palette[idx % len(palette)])
            draw_edges(frame_f, kp)
        cv2.imshow("Front Camera", frame_f)

    if not queue_side_results.empty():
        frame_s, people_s, latency_s = queue_side_results.get()
        for idx, kp in enumerate(people_s):
            draw_keypoints(frame_s, kp, color=palette[idx % len(palette)])
            draw_edges(frame_s, kp)
        cv2.imshow("Side Camera", frame_s)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam_front.release()
cam_side.release()
cv2.destroyAllWindows()