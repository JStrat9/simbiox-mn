# interfaces/runtime/static_camera_adapter.py
"""
Static camera-to-athlete adapter for pilot dual-camera mode.

In single-camera mode the legacy SessionPersonManager handles identity
resolution via IoU tracking.  In dual-camera mode each camera covers
exactly one station, so a static binding is sufficient and avoids tracker
coordinate collisions between cameras.

Usage:
    side_adapter  = StaticCameraSessionAdapter("athlete_1", session_state)
    front_adapter = StaticCameraSessionAdapter("athlete_2", session_state)

Each instance always resolves ANY centroid to the fixed session_person_id,
and reads the station directly from SessionState so no separate tracker is
needed.
"""

from __future__ import annotations

import numpy as np

from application.ports.process_person_ports import IdentityResolution
from domain.session.session_state import SessionState
from interfaces.runtime.station import Station


class StaticCameraSessionAdapter:
    """
    Identity resolver + station provider for one fixed athlete per camera.

    Implements the minimal surface required by process_person_uc:
      - resolve(centroid)                  → IdentityResolution
      - get_station(session_person_id)     → Station
      - release_missing_client_ids(ids)    → no-op (no tracker to maintain)
    """

    def __init__(self, session_person_id: str, session_state: SessionState) -> None:
        self._pid = session_person_id
        self._state = session_state

    def resolve(self, centroid: np.ndarray) -> IdentityResolution:
        return IdentityResolution(
            client_id=self._pid,
            session_person_id=self._pid,
        )

    def get_station(self, session_person_id: str) -> Station:
        station_id = self._state.assignments.get(self._pid, "station1")
        exercise = self._state.station_map.get(station_id, "squat")
        reps = self._state.reps.get(self._pid, 0)
        return Station(station_id=station_id, exercise=exercise, reps=reps)

    def release_missing_client_ids(self, current_ids: set) -> None:
        pass  # no tracker state to clean up
