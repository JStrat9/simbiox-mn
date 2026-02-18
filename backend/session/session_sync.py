from __future__ import annotations

from typing import Any, Mapping

from session.session_state import SessionState


def sync_session_state_for_person(
    session_state: SessionState,
    session_person_id: str,
    station_id: str,
    result: Mapping[str, Any],
    is_squat_station: bool,
) -> bool:
    changed = False

    if session_state.assignments.get(session_person_id) != station_id:
        session_state.set_assignment(
            session_person_id,
            station_id,
            increment_version=True,
        )
        changed = True

    if not is_squat_station:
        if session_state.errors.get(session_person_id, []) != []:
            session_state.set_errors(
                session_person_id,
                [],
                increment_version=True,
            )
            changed = True
        return changed

    if result.get("valid"):
        next_reps = max(0, int(result.get("reps", 0)))
        if session_state.reps.get(session_person_id, 0) != next_reps:
            session_state.set_reps(
                session_person_id,
                next_reps,
                increment_version=True,
            )
            changed = True

        next_errors = list(dict.fromkeys(result.get("errors", [])))
        if session_state.errors.get(session_person_id, []) != next_errors:
            session_state.set_errors(
                session_person_id,
                next_errors,
                increment_version=True,
            )
            changed = True

    return changed
