# feedback/event_mapper.py

class SquatEventAggregator:
    def __init__(self, max_clients: int = 6, error_hold_frames: int = 3):
        """
        max_clients: max number of clients
        error_hold_frames: number of frames to consider an error has desappeared
        """
        self.max_clients = max_clients
        self.prev_reps = {}
        self.active_errors = {}
        self.error_hold_frames = error_hold_frames

    def process(self, session_person_id: str, result: dict) -> list[dict]:
        events = []

        # --- REP_UPDATE ---
        prev = self.prev_reps.get(session_person_id, 0)
        curr = result.get("reps", 0)
        if curr != prev:
            events.append({
                "type": "REP_UPDATE",
                "session_person_id": session_person_id,
                "reps": curr
            })
            self.prev_reps[session_person_id] = curr

        # --- POSE_ERROR ---
        if session_person_id not in self.active_errors:
            self.active_errors[session_person_id] = {}
        
        # current errors on the current frame
        curr_errs = set(result.get("errors", []))
        # previous active errors
        prev_errs = set(self.active_errors[session_person_id].keys())

        # new errors -> emit
        for err in curr_errs - prev_errs:
            events.append({
                "type": "POSE_ERROR",
                "session_person_id": session_person_id,
                "exercise": "Squat",
                "errorCode": err
            })
            # Marck errors as active with hold 
            self.active_errors[session_person_id][err] = self.error_hold_frames
        
        # Already active errors -> refresh hold
        for err in curr_errs & prev_errs:
            self.active_errors[session_person_id][err] = self.error_hold_frames

        # Decrease hold for active errors
        for err in prev_errs - curr_errs:
            self.active_errors[session_person_id][err] -= 1
            if self.active_errors[session_person_id][err] <= 0:
                del self.active_errors[session_person_id][err]

        return events