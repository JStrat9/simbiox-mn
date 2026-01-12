# main.py

# TODO: ENTENDER CÓMO IDENTIFICAR QUÉ CLIENTE ESTÁ HACIENDO QUE EJERCICIO (ESTACIÓN) chatGPT:"identidad funcional dentro de una sesión."

import asyncio
import cv2
from queue import Queue
import time
import os
import psutil
import threading
import numpy as np

from feedback.event_mapper import SquatEventAggregator
from video.camera_worker import CameraWorker
from detectors.movenet_inference import MoveNet
from detectors.keypoints_movenet import choose_side, extract_side_keypoints
from detectors.squat_detector_manager import SquatDetectorManager
from utils.draw import draw_keypoints, draw_edges, draw_angles
from utils.draw_feedback import draw_feedback
from communication.websocket_server import emit_pose_error, emit_rep_update, start_server
from tracking.tracker_iou import CentroidTracker

from session.session_person_manager import SessionPersonManager
from config import MAX_PERSONS

session_manager = SessionPersonManager(
    max_persons=MAX_PERSONS, 
    t_active=0.8, t_lost=2.0, 
    distance_threshold=120.0
)

from config import CAMERA_FRONT_URL, CAMERA_SIDE_URL, MOVENET_TFLITE_MODEL

def get_centroid(keypoints):
    visible = [kp[:2] for kp in keypoints if kp[2] > 0.1] # kp = (x, y, score)
    if not visible:
        return np.array([0, 0])
    return np.mean(visible, axis=0)


def main():
    # Inicializar MoveNet
    print("[INFO] Cargando MoveNet...")
    movenet = MoveNet(str(MOVENET_TFLITE_MODEL))

    detector_manager = SquatDetectorManager(max_clients=6)

    # Inicializar cámaras con CameraWorker
    side_queue = Queue(maxsize=1)

    # front_cam = CameraWorker(CAMERA_FRONT_URL, front_queue, name="Front")
    side_cam  = CameraWorker(CAMERA_SIDE_URL, side_queue, name="Side")

    # front_cam.start()
    side_cam.start()

    palette = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]

    # Variables de performance
    process = psutil.Process(os.getpid())
    last_print = time.time()
    frames = 0

    print("[INFO] Iniciando loop principal...")

    aggregator = SquatEventAggregator()
    tracker = CentroidTracker(max_clients=6, distance_threshold=100)

    while True:
        # Obtener frames
        # if front_queue.empty() or side_queue.empty(): (CAMBIAR LINEA INFERIRO POR ESTA PARA DOS CAMARAS)
        if  side_queue.empty():
            time.sleep(0.001)
            continue

        current_client_ids = set()

        # -----------------------
        # Inferencia MoveNet
        # -----------------------
        # frame_f = front_queue.get()
        # people_f = movenet.run(frame_f)

        frame_s = side_queue.get()
        people_s = movenet.run(frame_s)

        # -----------------------
        # Analizar cada persona
        # -----------------------
        # for idx, person_kp in enumerate(people_f):
        #     side = choose_side(person_kp)
        #     # side_kp = extract_side_keypoints(person_kp, side)
        #    detector = detector_manager.get(client_id)
            # result = detector.analyze(person_kp)

            # events = aggregator.process(session_person_id, result)

        #     draw_feedback(
        #         frame_f,
        #         reps=feedback["reps"],
        #         error=feedback["error"]
        #     )

        # if result["feedback"]:
        #     error_data = {
        #         "reps": result["reps"],
        #         "feedback": result["feedback"],
        # "angles": result["angles"]
        #     }
        # send_error_threadsafe(error_data)

        #     print(f"[FRONT] Persona {idx}: lado={side}, resultado={result}")

        #     draw_keypoints(frame_f, person_kp, color=palette[idx % len(palette)])
        #     draw_edges(frame_f, person_kp)
        # draw_angles(frame_f, person_kp, result["angles"], side)

        for idx, person_kp in enumerate(people_s):
            side = choose_side(person_kp)
            # side_kp = extract_side_keypoints(person_kp, side)
            centroid = get_centroid(person_kp)
            try:
                client_id = tracker.get_client_id(centroid)
                session_person_id = session_manager.resolve_person(client_id, centroid)
            except RuntimeError:
                # If there are no available IDs, skip this person
                continue

            current_client_ids.add(client_id)

            detector = detector_manager.get(session_person_id)
            print(f"[SESSION] client_id={client_id} -> session_person_id={session_person_id}")

            result = detector.analyze(person_kp)

            # --- Process events ---
            events = aggregator.process(session_person_id, result)

            # --- Draw feedback ---
            draw_feedback(
                frame_s,
                reps=result.get("reps", ),
                error=result["errors"][0] if result.get("errors") else ""
            )

            draw_keypoints(frame_s, person_kp, color=palette[idx % len(palette)])
            draw_edges(frame_s, person_kp)
            draw_angles(frame_s, person_kp, result.get("angles", {}), side)

            # --- Emit events ---
            for event in events:
                if event["type"] == "REP_UPDATE":
                    emit_rep_update(event["session_person_id"], event["reps"])
                elif event["type"] == "POSE_ERROR":
                    emit_pose_error(event["session_person_id"], event["exercise"], event["errorCode"])
                # print(f"[MAIN] Envaindo error a WebSocket: {error_data}", flush=True)
                # send_error_threadsafe(error_data)

            print(f"[SIDE] Persona {idx}: lado={side}, resultado={result}")

        # --- Release missing clients ---
        print(f"[TRACK] active clients this frame: {current_client_ids}")
        print("[DEBUG] people detected:", len(people_s))
        tracker.release_missing(current_client_ids)

        # --- Show frames ---
        # cv2.imshow("Front Camera", frame_f)
        cv2.imshow("Side Camera", frame_s)

        # --- Performance (FPS / CPU / RAM) ---
        frames += 1
        now = time.time()
        if now - last_print >= 1.0:
            fps = frames / (now - last_print)
            cpu = psutil.cpu_percent()
            ram = process.memory_info().rss / 1024 / 1024

            print(f"[PERF][MAIN] fps={fps:.0f} cpu={cpu}% ram={ram:.0f}MB")

            last_print = now
            frames = 0

        # --- Salida ---
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # --- Limpiar ---
    # front_cam.stop()
    side_cam.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    ws_ready_event = threading.Event()

    def run_ws_server():
        asyncio.run(start_server(ready_event=ws_ready_event))
    # WebSocket server thread
    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()

    # Esperar a que el servidor WebSocket esté listo
    print("[INFO] Esperando a que el servidor WebSocket esté listo...")
    ws_ready_event.wait(timeout=5.0)
    print("[INFO] Servidor WebSocket listo!")
    
    # Pequeña pausa adicional para asegurar que todo está inicializado
    time.sleep(0.5)

    main()
