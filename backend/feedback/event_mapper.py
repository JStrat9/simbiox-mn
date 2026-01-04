# feedback/event_mapper.py

class SquatEventAggregator:
    def __init__(self):
        self.prev_reps = {}
        self.prev_errors = {}

    def process(self, client_id: str, result: dict) -> list[dict]:
        events = []

        # --- REP_UPDATE ---
        prev = self.prev_reps.get(client_id, 0)
        curr = result.get("reps", 0)

        if curr != prev:
            events.append({
                "type": "REP_UPDATE",
                "clientId": client_id,
                "reps": curr
            })
            self.prev_reps[client_id] = curr

        # --- POSE_ERROR ---
        prev_errs = self.prev_errors.get(client_id, [])
        curr_errs = result.get("errors", [])

        for err in curr_errs:
            if err not in prev_errs:
                events.append({
                    "type": "POSE_ERROR",
                    "clientId": client_id,
                    "exercise": "Squat",
                    "errorCode": err
                })
        self.prev_errors[client_id] = curr_errs

        return events