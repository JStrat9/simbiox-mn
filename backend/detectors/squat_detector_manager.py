# detectors/squat_detector_manager.py

from detectors.squat_detector import SquatDetector

class SquatDetectorManager:
    def __init__(self, max_clients: int = 6):
        self.detectors: dict[str, SquatDetector] = {}
        self.max_clients = max_clients

    def get(self, client_id: str, exercise: str = "squat") -> SquatDetector:
        """
        Returns a detector for the given client_id.
        If the client_id is not in the dictionary, a new detector is created.
        """
        if client_id not in self.detectors:
            if len(self.detectors) >= self.max_clients:
                raise RuntimeError("Max clients_id reached")
            
            self.detectors[client_id] = SquatDetector()
            print(f"New detector create for client_id {client_id}")

        return self.detectors[client_id]

    def reset(self, client_id: str):
        if client_id in self.detectors:
            self.detectors[client_id] = SquatDetector()

    def clear_all(self):
        self.detectors.clear()

    def clear_reviewed_errors(self, client_id: str):
        detector = self.detectors.get(client_id)
        if detector is None:
            return
        detector.clear_reviewed_errors()
