# session/session_snapshot.py

import time

from session.error_normalizer import (
    build_errors_v2_from_codes,
    canonicalize_errors_v2,
    error_codes_from_errors_v2,
)
from session.session_state import SessionState


def _athlete_sort_key(athlete_id: str):
    try:
        return (int(athlete_id.split("_")[1]), athlete_id)
    except (IndexError, ValueError):
        return (10**9, athlete_id)


def build_session_update(session_state: SessionState) -> dict:
    athlete_ids = (
        set(session_state.assignments.keys())
        | set(session_state.reps.keys())
        | set(session_state.errors.keys())
        | set(getattr(session_state, "errors_v2", {}).keys())
    )

    athletes = {}
    for athlete_id in sorted(athlete_ids, key=_athlete_sort_key):
        raw_errors_v2 = getattr(session_state, "errors_v2", {}).get(athlete_id)
        if raw_errors_v2:
            errors_v2 = canonicalize_errors_v2(raw_errors_v2)
        else:
            errors_v2 = build_errors_v2_from_codes(
                session_state.errors.get(athlete_id, [])
            )
        # Legacy `errors` remains for compatibility and is derived from `errors_v2`.
        errors = error_codes_from_errors_v2(errors_v2)

        athletes[athlete_id] = {
            "station_id": session_state.assignments.get(athlete_id),
            "reps": int(session_state.reps.get(athlete_id, 0)),
            "errors": errors,
            "errors_v2": [
                {
                    "code": error["code"],
                    "message_key": error["message_key"],
                    "severity": error["severity"],
                    "metadata": dict(error["metadata"]),
                }
                for error in errors_v2
            ],
        }

    stations = {
        station_id: {"exercise": exercise}
        for station_id, exercise in session_state.station_map.items()
    }

    timestamp = int(getattr(session_state, "updated_at", int(time.time())))
    version = int(getattr(session_state, "version", 0))

    return {
        "type": "SESSION_UPDATE",
        "version": version,
        "timestamp": timestamp,
        "athletes": athletes,
        "stations": stations,
    }
