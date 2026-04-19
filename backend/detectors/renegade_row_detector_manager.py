# detectors/renegade_row_detector_manager.py

from detectors.renegade_row_detector import RenegadeRowDetector


class RenegadeRowDetectorManager:
    def __init__(self, max_clients: int = 6):
        self.detectors: dict[str, RenegadeRowDetector] = {}
        self.max_clients = max_clients

    def get(self, client_id: str, exercise: str = "renegade_row") -> RenegadeRowDetector:
        if client_id not in self.detectors:
            if len(self.detectors) >= self.max_clients:
                raise RuntimeError("Max clients_id reached")
            self.detectors[client_id] = RenegadeRowDetector()
            print(f"New detector created for client_id {client_id}")
        return self.detectors[client_id]

    def reset(self, client_id: str):
        if client_id in self.detectors:
            self.detectors[client_id] = RenegadeRowDetector()

    def clear_all(self):
        self.detectors.clear()
