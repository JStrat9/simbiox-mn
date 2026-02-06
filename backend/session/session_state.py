# session_state.py

class SessionState:
    def __init__(self):
        self.rotation_index = 0
        # Define order before starting the traning session
        self.station_order = ["station1", "station2", "station3", "station4", "station5", "station6"]
        # Athlete -> current station
        self.assignments = {
            f"athlete_{i}": f"station{i}" for i in range(1, 7)
        }

        # Athlete -> reps contadas
        self.reps: dict[str, int] = {
            f"athlete_{i}": 0 for i in range(1, 7)
        }

        self.station_map: dict[str, str] = {
        "station1": "squat",
        "station2": "pushup",
        "station3": "pullup",
        "station4": "lunges",
        "station5": "plank",
        "station6": "jumping_jack",
    }