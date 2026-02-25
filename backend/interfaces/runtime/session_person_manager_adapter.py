from __future__ import annotations

from typing import cast

import numpy as np

from application.ports.process_person_ports import IdentityResolution, StationView
from application.ports.session_person_manager_ports import RuntimeSessionManagerPort
from domain.session.session_state import SessionState
from interfaces.runtime.session_person_manager import SessionPersonManager


class LegacySessionPersonManagerAdapter(RuntimeSessionManagerPort):
    """
    Adapter from legacy session manager implementation to application runtime ports.
    """

    def __init__(self, manager: SessionPersonManager):
        self._manager = manager

    def resolve(self, centroid: np.ndarray) -> IdentityResolution:
        client_id, session_person_id = self._manager.resolve_identity(centroid)
        return IdentityResolution(
            client_id=client_id,
            session_person_id=session_person_id,
        )

    def get_station(self, session_person_id: str) -> StationView:
        # Concrete return type from legacy manager satisfies StationView protocol.
        return cast(StationView, self._manager.get_station(session_person_id))

    def release_missing_client_ids(self, current_ids: set[str]) -> None:
        self._manager.release_missing_client_ids(current_ids)

    def assign_station(self, session_person_id: str, station_id: str) -> None:
        self._manager.assign_station(session_person_id, station_id)


def build_legacy_session_person_manager_adapter(
    *,
    session_state: SessionState,
    max_persons: int,
    reassignment_timeout: float = 2.0,
    t_active: float = 0.8,
    t_lost: float = 2.5,
    distance_threshold: float = 120.0,
) -> RuntimeSessionManagerPort:
    manager = SessionPersonManager(
        max_persons=max_persons,
        reassignment_timeout=reassignment_timeout,
        t_active=t_active,
        t_lost=t_lost,
        distance_threshold=distance_threshold,
    )
    manager.session_state = session_state
    return LegacySessionPersonManagerAdapter(manager)


__all__ = [
    "LegacySessionPersonManagerAdapter",
    "build_legacy_session_person_manager_adapter",
]
