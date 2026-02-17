# feedback/event_mapper.py


class SquatTelemetryAggregator:
    """
    Internal per-athlete telemetry helper.

    This module no longer produces transport-level websocket events.
    It only computes frame-to-frame deltas that can be logged or exported
    to internal observability pipelines.
    """

    def __init__(self, max_clients: int = 6, error_hold_frames: int = 3):
        self.max_clients = max_clients
        self.prev_reps: dict[str, int] = {}
        self.active_errors: dict[str, dict[str, int]] = {}
        self.error_hold_frames = error_hold_frames

    def observe(self, athlete_id: str, result: dict) -> dict:
        prev_reps = self.prev_reps.get(athlete_id, 0)
        curr_reps = int(result.get("reps", 0))
        rep_changed = curr_reps != prev_reps
        if rep_changed:
            self.prev_reps[athlete_id] = curr_reps

        if athlete_id not in self.active_errors:
            self.active_errors[athlete_id] = {}

        curr_errors = set(result.get("errors", []))
        prev_errors = set(self.active_errors[athlete_id].keys())

        new_errors = sorted(curr_errors - prev_errors)
        resolved_errors = sorted(prev_errors - curr_errors)

        for error_code in curr_errors & prev_errors:
            self.active_errors[athlete_id][error_code] = self.error_hold_frames

        for error_code in new_errors:
            self.active_errors[athlete_id][error_code] = self.error_hold_frames

        for error_code in list(resolved_errors):
            self.active_errors[athlete_id][error_code] -= 1
            if self.active_errors[athlete_id][error_code] <= 0:
                del self.active_errors[athlete_id][error_code]

        return {
            "athlete_id": athlete_id,
            "rep_changed": rep_changed,
            "reps": curr_reps,
            "new_errors": new_errors,
            "active_errors": sorted(self.active_errors[athlete_id].keys()),
        }

