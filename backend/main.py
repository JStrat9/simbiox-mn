# main.py

import asyncio
import cv2
from queue import Queue
import time
import os
import psutil
import threading

from feedback.event_mapper import map_squat_event
from video.camera_worker import CameraWorker
from detectors.movenet_inference import MoveNet
from detectors.keypoints_movenet import choose_side, extract_side_keypoints
from detectors.squat_detector import SquatDetector
from utils.draw import draw_keypoints, draw_edges, draw_angles
from utils.draw_feedback import draw_feedback
from communication.websocket_server import emit_pose_error, emit_rep_update, start_server

from config import CAMERA_FRONT_URL, CAMERA_SIDE_URL, MOVENET_TFLITE_MODEL


def main():
    # -----------------------
    # Inicializar MoveNet
    # -----------------------
    print("[INFO] Cargando MoveNet...")
    movenet = MoveNet(str(MOVENET_TFLITE_MODEL))

    # -----------------------
    # Inicializar SquatDetector
    # -----------------------
    squat_detector = SquatDetector()

    # -----------------------
    # Inicializar cámaras con CameraWorker
    # -----------------------
    # front_queue = Queue(maxsize=1)
    side_queue = Queue(maxsize=1)

    # front_cam = CameraWorker(CAMERA_FRONT_URL, front_queue, name="Front")
    side_cam  = CameraWorker(CAMERA_SIDE_URL, side_queue, name="Side")

    # front_cam.start()
    side_cam.start()

    palette = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]

    # -----------------------
    # Variables de performance
    # -----------------------
    process = psutil.Process(os.getpid())
    last_print = time.time()
    frames = 0

    print("[INFO] Iniciando loop principal...")

    client_prev_errors: dict[str, list[str]] = {}
    client_prev_reps: dict[str, int] = {}
    palette = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]

    while True:
        # -----------------------
        # Obtener frames
        # -----------------------
        # if front_queue.empty() or side_queue.empty(): (CAMBIAR LINEA INFERIRO POR ESTA PARA DOS CAMARAS)
        if  side_queue.empty():
            time.sleep(0.001)
            continue

        # frame_f = front_queue.get()
        frame_s = side_queue.get()

        # -----------------------
        # Inferencia MoveNet
        # -----------------------
        # people_f = movenet.run(frame_f)
        people_s = movenet.run(frame_s)

        # -----------------------
        # Analizar cada persona
        # -----------------------
        # for idx, person_kp in enumerate(people_f):
        #     side = choose_side(person_kp)
        #     # side_kp = extract_side_keypoints(person_kp, side)
        #     result = squat_detector.analyze(person_kp)
        #     feedback = map_squat_feedback(result)

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
            client_id = str(idx + 1)
            result = squat_detector.analyze(person_kp)

            events = []

            # -----------------------
            # REP_UPDATE (solo si cambia)
            # -----------------------
            prev_reps = client_prev_reps.get(client_id, 0)
            current_reps = result.get("reps", 0)

            if current_reps != prev_reps:
                events.append({
                    "type": "REP_UPDATE",
                    "clientId": client_id,
                    "reps": current_reps

                })
                client_prev_reps[client_id] = current_reps

            # -----------------------
            # POSE_ERROR (como ya haces)
            # -----------------------
            prev_errors = client_prev_errors.get(client_id, [])
            error_events = map_squat_event(client_id, result, prev_errors)

            events.extend(
                e for e in error_events if e["type"] == "POSE_ERROR"
            )

            client_prev_errors[client_id] = result.get("errors", [])

            draw_feedback(
                frame_s,
                reps=result.get("reps", ),
                error=result.get("feedback") or (result.get("errors")[0] if result.get("errors") else "")
            )

            for event in events:
                if event["type"] == "REP_UPDATE":
                    emit_rep_update(event["clientId"], event["reps"])
                elif event["type"] == "POSE_ERROR":
                    emit_pose_error(event["clientId"], event["exercise"], event["errorCode"])
                # print(f"[MAIN] Envaindo error a WebSocket: {error_data}", flush=True)
                # send_error_threadsafe(error_data)


            print(f"[SIDE] Persona {idx}: lado={side}, resultado={result}")

            draw_keypoints(frame_s, person_kp, color=palette[idx % len(palette)])
            draw_edges(frame_s, person_kp)
            draw_angles(frame_s, person_kp, result["angles"], side)

        # -----------------------
        # Mostrar frames
        # -----------------------
        # cv2.imshow("Front Camera", frame_f)
        cv2.imshow("Side Camera", frame_s)

        # -----------------------
        # Performance (FPS / CPU / RAM)
        # -----------------------
        frames += 1
        now = time.time()
        if now - last_print >= 1.0:
            fps = frames / (now - last_print)
            cpu = psutil.cpu_percent()
            ram = process.memory_info().rss / 1024 / 1024

            print(f"[PERF][MAIN] fps={fps:.0f} cpu={cpu}% ram={ram:.0f}MB")

            last_print = now
            frames = 0

        # -----------------------
        # Salida
        # -----------------------
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # -----------------------
    # Limpiar
    # -----------------------
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
