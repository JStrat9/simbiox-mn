from __future__ import annotations

from typing import Protocol


class RuntimeStationSyncPort(Protocol):
    def sync(self, session_person_id: str, station_id: str) -> None:
        ...
