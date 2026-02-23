# session/session_snapshot.py

import time

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
        athletes[athlete_id] = {
            "station_id": session_state.assignments.get(athlete_id),
            "reps": int(session_state.reps.get(athlete_id, 0)),
            "errors": list(session_state.errors.get(athlete_id, [])),
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
