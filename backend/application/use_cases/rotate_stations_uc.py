from __future__ import annotations

from typing import Dict

from application.projections.session_update_projection import (
    build_session_update_projection,
)
from application.ports.runtime_station_sync import RuntimeStationSyncPort
from domain.session.rotation_policy import rotate_stations
from domain.session.session_state import SessionState


def _sync_runtime_stations(
    assignments: Dict[str, str],
    runtime_station_sync: RuntimeStationSyncPort | None,
) -> None:
    if runtime_station_sync is None:
        print("[WS][WARN] rotate station handler not registered", flush=True)
        return

    for session_person_id, station_id in assignments.items():
        runtime_station_sync.sync(session_person_id, station_id)


def rotate_stations_use_case(
    *,
    session_state: SessionState,
    runtime_station_sync: RuntimeStationSyncPort | None = None,
) -> dict:
    new_assignments = rotate_stations(session_state)
    print("[DEBUG ROTATE STATIONS] New assignments:", new_assignments, flush=True)
    _sync_runtime_stations(new_assignments, runtime_station_sync)
    return build_session_update_projection(session_state)
