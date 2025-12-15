# detectors/keypoints_movenet.py

import numpy as np

# MoveNet MultiPose keypoint indices (17 keypoints)
KP = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}

# Helper list for easy grouping
LEFT_SIDE = [
    KP["left_shoulder"],
    KP["left_elbow"],
    KP["left_wrist"],
    KP["left_hip"],
    KP["left_knee"],
    KP["left_ankle"],
]

RIGHT_SIDE = [
    KP["right_shoulder"],
    KP["right_elbow"],
    KP["right_wrist"],
    KP["right_hip"],
    KP["right_knee"],
    KP["right_ankle"],
]

def choose_side(person_kp: np.ndarray) -> str:
    """
    Decide si usar el lado izquierdo o derecho según
    qué lado tenga más keypoints con mayor score.
    person_kp: array shape (17, 3) with [y, x, confidence]
    """

    left_scores = np.sum([person_kp[i][2] for i in LEFT_SIDE])  # confidence is at index 2
    right_scores = np.sum([person_kp[i][2] for i in RIGHT_SIDE])

    return "left" if left_scores >= right_scores else "right"

def extract_side_keypoints(person_kp: np.ndarray, side: str):
    """
    Devuelve un dict con shoulder, hip, knee, ankle del lado elegido.
    person_kp: array shape (17, 3) with [y, x, confidence]
    Cada punto devuelto es: np.array([y, x, confidence])
    """

    if side == "left":
        shoulder = person_kp[KP["left_shoulder"]]
        hip      = person_kp[KP["left_hip"]]
        knee     = person_kp[KP["left_knee"]]
        ankle    = person_kp[KP["left_ankle"]]
    else:
        shoulder = person_kp[KP["right_shoulder"]]
        hip      = person_kp[KP["right_hip"]]
        knee     = person_kp[KP["right_knee"]]
        ankle    = person_kp[KP["right_ankle"]]

    return {
        "shoulder": np.array(shoulder),
        "hip": np.array(hip),
        "knee": np.array(knee),
        "ankle": np.array(ankle),
    }