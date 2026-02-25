from __future__ import annotations

from typing import Protocol, runtime_checkable

from application.ports.process_person_ports import (
    IdentityResolver,
    StationProvider,
)


@runtime_checkable
class RuntimePresenceTrackerPort(Protocol):
    """Tracks missing physical client IDs across runtime frames."""

    def release_missing_client_ids(self, current_ids: set[str]) -> None:
        ...


@runtime_checkable
class RuntimeStationAssignerPort(Protocol):
    """Synchronizes runtime station assignment for one logical person."""

    def assign_station(self, session_person_id: str, station_id: str) -> None:
        ...


@runtime_checkable
class RuntimeSessionManagerPort(
    IdentityResolver,
    StationProvider,
    RuntimePresenceTrackerPort,
    RuntimeStationAssignerPort,
    Protocol,
):
    """Runtime-facing contract for person identity + station responsibilities."""

    pass


__all__ = [
    "RuntimePresenceTrackerPort",
    "RuntimeStationAssignerPort",
    "RuntimeSessionManagerPort",
]
