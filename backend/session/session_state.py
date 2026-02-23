# session_state.py

import time


class SessionState:
    def __init__(self):
        self.rotation_index = 0
        self.version = 0
        self.updated_at = int(time.time())

        # Define order before starting the training session
        self.station_order = [
            "station1",
            "station2",
            "station3",
            "station4",
            "station5",
            "station6",
        ]

        # Athlete -> current station
        self.assignments: dict[str, str] = {
            f"athlete_{i}": f"station{i}" for i in range(1, 7)
        }

        # Athlete -> counted reps
        self.reps: dict[str, int] = {
            f"athlete_{i}": 0 for i in range(1, 7)
        }

        # Athlete -> active error list
        self.errors: dict[str, list[str]] = {
            f"athlete_{i}": [] for i in range(1, 7)
        }

        # Station catalog is exposed to frontend via SESSION_UPDATE.stations.
        self.station_map: dict[str, str] = {
            "station1": "",
            "station2": "pushup",
            "station3": "pullup",
            "station4": "lunges",
            "station5": "plank",
            "station6": "jumping_jack",
        }

    def _touch(self, increment_version: bool = False):
        self.updated_at = int(time.time())
        if increment_version:
            self.version += 1

    def set_assignment(self, athlete_id: str, station_id: str, increment_version: bool = False):
        if self.assignments.get(athlete_id) == station_id:
            return
        self.assignments[athlete_id] = station_id
        self._touch(increment_version=increment_version)

    def set_reps(self, athlete_id: str, reps: int, increment_version: bool = False):
        safe_reps = max(0, int(reps))
        if self.reps.get(athlete_id) == safe_reps:
            return
        self.reps[athlete_id] = safe_reps
        self._touch(increment_version=increment_version)

    def set_errors(self, athlete_id: str, errors: list[str], increment_version: bool = False):
        normalized_errors = list(dict.fromkeys(errors or []))
        if self.errors.get(athlete_id) == normalized_errors:
            return
        self.errors[athlete_id] = normalized_errors
        self._touch(increment_version=increment_version)
