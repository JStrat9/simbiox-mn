# test_movenet.py

import cv2
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import time

# -----------------------
# Configuración
# -----------------------
VIDEO_SOURCE = "rtsp://admin:JLD@SimbioxMVP4928@192.168.1.16:554/h264Preview_01_sub"  # 0 = webcam local, o reemplaza con URL de cámara IP
MODEL_URL = "https://tfhub.dev/google/movenet/multipose/lightning/1"
INPUT_SIZE = 192  # MoveNet Lightning espera 192x192

# -----------------------
# Cargar modelo MoveNet
# -----------------------
model = hub.load(MODEL_URL)
movenet = model.signatures['serving_default']

KEYPOINT_EDGES = {
    (0,1), (0,2), (1,3), (2,4),
    (0,5), (0,6), (5,7), (7,9),
    (6,8), (8,10), (5,6), (5,11),
    (6,12), (11,12), (11,13), (13,15),
    (12,14), (14,16)
}

# -----------------------
# Función para procesar frame
# -----------------------
def detect_pose(frame):
    img = tf.image.resize_with_pad(tf.expand_dims(frame, axis=0), 256, 256)
    input_img = tf.cast(img, dtype=tf.int32)

    outputs = movenet(input_img)
    poses = outputs['output_0'].numpy()[0]

    people = []
    for person in poses:
        kp = person[:51].reshape((17, 3))  # 17 keypoints
        pose_score = person[55]

        if pose_score > 0.2:  # filtro mínimo
            people.append(kp)

    return people


def draw_keypoints(frame, keypoints, color=(0,255,0), threshold=0.3):
    h, w, _ = frame.shape
    for y, x, c in keypoints:
        if c > threshold:
            cv2.circle(frame, (int(x*w), int(y*h)), 4, color, -1)


def draw_edges(frame, keypoints, threshold=0.3):
    h, w, _ = frame.shape
    for i, j in KEYPOINT_EDGES:
        y1, x1, c1 = keypoints[i]
        y2, x2, c2 = keypoints[j]
        if c1 > threshold and c2 > threshold:
            p1 = (int(x1*w), int(y1*h))
            p2 = (int(x2*w), int(y2*h))
            cv2.line(frame, p1, p2, (255, 255, 255), 2)


# Video o RTSP
cap = cv2.VideoCapture(VIDEO_SOURCE)
# cap = cv2.VideoCapture("rtsp://admin:password@192.168.1.16:554/h264Preview_01_sub")

t0 = time.time()
frames = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    people = detect_pose(img_rgb)

    # Colores distintos por persona
    palette = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]

    for idx, kp in enumerate(people):
        color = palette[idx % len(palette)]
        draw_keypoints(frame, kp, color)
        draw_edges(frame, kp)

    # FPS
    frames += 1
    if frames % 10 == 0:
        fps = frames / (time.time() - t0)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("MoveNet MultiPose", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
