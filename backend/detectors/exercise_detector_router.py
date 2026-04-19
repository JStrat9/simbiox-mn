# detectors/exercise_detector_router.py

from detectors.squat_detector_manager import SquatDetectorManager
from detectors.renegade_row_detector_manager import RenegadeRowDetectorManager


class ExerciseDetectorRouter:
    def __init__(self, max_clients: int = 6):
        self._squat = SquatDetectorManager(max_clients=max_clients)
        self._renegade_row = RenegadeRowDetectorManager(max_clients=max_clients)

    def get(self, session_person_id: str, exercise: str):
        if exercise == "squat":
            return self._squat.get(session_person_id)
        if exercise == "renegade_row":
            return self._renegade_row.get(session_person_id)
        raise ValueError(f"No detector for exercise {exercise!r}")
