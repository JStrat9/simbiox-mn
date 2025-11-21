# test_dual_cameras_multipose_threaded.py
from capture.camera_front import FrontCamera
from capture.camera_side import SideCamera
from utils.performance import PerformanceLogger
import cv2
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import time
import threading
from queue import Queue

# -----------------------
# Configuración MoveNet
# -----------------------
MODEL_URL = "https://tfhub.dev/google/movenet/multipose/lightning/1"
INPUT_SIZE = 256  # MoveNet MultiPose espera 256x256

KEYPOINT_EDGES = {
    (0,1), (0,2), (1,3), (2,4),
    (0,5), (0,6), (5,7), (7,9),
    (6,8), (8,10), (5,6), (5,11),
    (6,12), (11,12), (11,13), (13,15),
    (12,14), (14,16)
}

# -----------------------
# Funciones MoveNet
# -----------------------
print("[INFO] Cargando modelo MoveNet MultiPose...")
model = hub.load(MODEL_URL)
movenet = model.signatures['serving_default']

def detect_pose(frame):
    img = tf.image.resize_with_pad(tf.expand_dims(frame, axis=0), INPUT_SIZE, INPUT_SIZE)
    input_img = tf.cast(img, dtype=tf.int32)
    outputs = movenet(input_img)
    poses = outputs['output_0'].numpy()[0]

    people = []
    for person in poses:
        kp = person[:51].reshape((17,3))
        score = person[55]
        if score > 0.2:
            people.append(kp)
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

# Queues para pasar frames y resultados entre hilos
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
        time.sleep(0.001)  # pequeño sleep para no saturar CPU

# -----------------------
# Hilos de inferencia MoveNet
# -----------------------
def inference_thread(frame_queue, result_queue, name):
    while True:
        if frame_queue.empty():
            time.sleep(0.001)
            continue
        frame = frame_queue.get()
        t0 = time.time()
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        people = detect_pose(img_rgb)
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
    # Front
    if not queue_front_results.empty():
        frame_f, people_f, latency_f = queue_front_results.get()
        for idx, kp in enumerate(people_f):
            draw_keypoints(frame_f, kp, color=palette[idx % len(palette)])
            draw_edges(frame_f, kp)
        cv2.imshow("Front Camera", frame_f)

    # Side
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
