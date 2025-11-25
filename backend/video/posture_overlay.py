import cv2
import numpy as np
import asyncio
from communication.websocket_server import send_error_threadsafe
from detectors.keypoints_movenet import KEYPOINT


def analyze_and_draw(frame, frame_width, frame_height, detector, landmarks, loop, client_id="1"):

    ERRORS = [
                        "Bajaste poco",
                        "Demasiado profundo",
                        "Inclinas el torso",
                        "Rodillas demasiado adelantadas"
    ]
    
    image = frame

    if landmarks is not None and len(landmarks) > 0:
         try:
            analysis = detector.analyze(landmarks)

            feedback = analysis.get("feedback", "")
            print(f"[POSTURE] feedback_raw={feedback!r} last_sent{getattr(detector, 'last_feedback_sent', None)!r}", flush=True)

            if feedback and any(err in feedback for err in ERRORS) and feedback != getattr(detector, "last_feedback_sent", None):
                        error_data = {
                            "clientId": client_id,
                            "feedback": feedback,
                            "phase": detector.squat_stage
                        }
                        print(f"[POSTURE] scheduling send_error: {error_data}", flush=True)
                        # usar la función threadsafe del servidor WS (no usar aquí run_coroutine_threadsafe directamente)
                        send_error_threadsafe(error_data)
                        detector.last_feedback_sent = feedback


            # --- Draw information on the frame --- #
            angles = analysis["angles"]
            joints = analysis["joints"]
            minmax = analysis["minmax"]

                    # Texto general
            cv2.putText(image, f"Repeticiones: {analysis['counter']}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            # cv2.putText(image, f"Ángulo rodilla: {int(angles['knee'])}°", (10, 60),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            # cv2.putText(image, f"Ángulo cadera: {int(angles['hip'])}°", (10, 90),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            # cv2.putText(image, f"Ángulo codo: {int(angles['elbow'])}°", (10, 120),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.putText(image, f"Min rodilla: {int(minmax['min_knee'])}° Max: {int(minmax['max_knee'])}°", (10, 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(image, f"Min cadera: {int(minmax['min_hip'])}° Max: {int(minmax['max_hip'])}°", (10, 170),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(image, f"Min codo: {int(minmax['min_elbow'])}° Max: {int(minmax['max_elbow'])}°", (10, 190),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            color = (0, 255, 0) 
                    
            feedback_text = analysis["feedback"] or ""
            if isinstance(feedback_text, list):
                feedback_text = " | ".join(map(str, feedback_text))
            cv2.putText(image, feedback_text, (10, 220),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                # cv2.putText(image, f"Tracking: {'Activo' if analysis['detection_active'] else 'Perdido'}", (10, 250),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                # Coordenadas de articulaciones
            if analysis['detection_active']:
                  for name, point, color in zip(
                            ["knee", "hip", "elbow", "ankle"], 
                            [joints["knee"], joints["hip"], joints["elbow"], joints["ankle"]],
                            [(0,255,255), (255,0,255), (0,255,0), (255,255,0)]
                  ):
                            if point:
                                px, py = point  
                                abs_x = int(px * frame_width)
                                abs_y = int(py * frame_height)


                                coords = (abs_x, abs_y)
                                cv2.putText(image, f"{int(angles[name])}°", coords, 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

         except Exception as e:
            print(f"Error de análisis: {e}")
            import traceback
            traceback.print_exc() # Print the traceback for debugging
            cv2.putText(image, "Error de detección", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return image  