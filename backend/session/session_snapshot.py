from application.projections.session_update_projection import (
    build_session_update_projection,
)
from session.session_state import SessionState


def build_session_update(session_state: SessionState) -> dict:
    # Compatibility shim for legacy imports during Fase 2.4 migration.
    return build_session_update_projection(session_state)
