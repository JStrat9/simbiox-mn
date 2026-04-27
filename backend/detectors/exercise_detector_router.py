# detectors/exercise_detector_router.py

from detectors.squat_detector_manager import SquatDetectorManager
from detectors.renegade_row_detector_manager import RenegadeRowDetectorManager


class ExerciseDetectorRouter:
    def __init__(self, max_clients: int = 6):
        self._squat = SquatDetectorManager(max_clients=max_clients)
        self._renegade_row = RenegadeRowDetectorManager(max_clients=max_clients)
        self._last_exercise: dict[str, str] = {}

    def _reset_previous_detector_if_needed(
        self,
        session_person_id: str,
        exercise: str,
    ) -> None:
        previous = self._last_exercise.get(session_person_id)
        if previous == exercise:
            return

        if previous == "squat":
            self._squat.reset(session_person_id)
        elif previous == "renegade_row":
            self._renegade_row.reset(session_person_id)

        self._last_exercise[session_person_id] = exercise

    def get(self, session_person_id: str, exercise: str):
        if exercise not in {"squat", "renegade_row"}:
            raise ValueError(f"No detector for exercise {exercise!r}")

        self._reset_previous_detector_if_needed(session_person_id, exercise)
        if exercise == "squat":
            return self._squat.get(session_person_id)
        return self._renegade_row.get(session_person_id)

    def clear_reviewed_errors(self, session_person_id: str) -> None:
        self._squat.clear_reviewed_errors(session_person_id)
        self._renegade_row.clear_reviewed_errors(session_person_id)
