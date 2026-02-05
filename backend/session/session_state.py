# session_state.py

class SessionState:
    def __init__(self):
        self.rotation_index = 0
        # Define order before starting the traning session
        self.station_order = ["station1", "station2", "station3", "station4", "station5", "station6"]
        # Athlete -> current station
        self.assignments = {
            "athlete_1": "station1",
            "athlete_2": "station2",
            "athlete_3": "station3",
            "athlete_4": "station4",
            "athlete_5": "station5",
            "athlete_6": "station6",
        }

        self.reps: dict[str, int] = {}  