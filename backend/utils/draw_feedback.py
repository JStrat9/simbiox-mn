# utils/draw_feedback.py

import cv2
from typing import Optional

def draw_feedback(
        frame,
        reps: Optional[int],
        error: Optional[str],
        origin=(20, 40)
):
    """
    Draws feedback information on the given video frame.
    """

    x, y = origin

    if reps is not None:
        cv2.putText(
            frame,
            f"Reps: {reps}",
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    
    if error:
        cv2.putText(
            frame,
            f"Error. {error}",
            (x, y + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )