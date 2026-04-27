from __future__ import annotations

from application.projections.session_update_projection import (
    build_session_update_projection,
)
from application.ports.runtime_reviewed_errors_sync import RuntimeReviewedErrorsSyncPort
from domain.session.session_state import SessionState


def _clear_session_errors(session_state: SessionState) -> None:
    athlete_ids = (
        set(session_state.assignments.keys())
        | set(session_state.errors.keys())
        | set(getattr(session_state, "errors_v2", {}).keys())
    )

    for session_person_id in sorted(athlete_ids):
        session_state.set_errors_v2(
            session_person_id,
            [],
            increment_version=True,
        )


def _clear_runtime_reviewed_errors(
    session_state: SessionState,
    runtime_reviewed_errors_sync: RuntimeReviewedErrorsSyncPort | None,
) -> None:
    if runtime_reviewed_errors_sync is None:
        print("[WS][WARN] clear reviewed errors handler not registered", flush=True)
        return

    for session_person_id in sorted(session_state.assignments.keys()):
        runtime_reviewed_errors_sync.clear(session_person_id)


def clear_reviewed_errors_use_case(
    *,
    session_state: SessionState,
    runtime_reviewed_errors_sync: RuntimeReviewedErrorsSyncPort | None = None,
) -> dict:
    _clear_session_errors(session_state)
    _clear_runtime_reviewed_errors(session_state, runtime_reviewed_errors_sync)
    return build_session_update_projection(session_state)
