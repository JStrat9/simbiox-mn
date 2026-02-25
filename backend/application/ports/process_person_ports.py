from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

import numpy as np

from domain.session.session_state import SessionState


@runtime_checkable
class StationView(Protocol):
    """Minimal station view required by process_person use case."""

    station_id: str
    exercise: str
    reps: int


@dataclass(frozen=True)
class IdentityResolution:
    """Physical-to-logical identity resolution result."""

    client_id: str
    session_person_id: str


@dataclass(frozen=True)
class ProcessPersonOutput:
    """
    Output contract for processing one detected person.

    Functional output fields are `session_person_id`, `station`, `result`,
    `state_changed`, `is_squat_station`, and `side`.
    """

    skipped: bool
    skip_reason: str | None
    client_id: str | None
    session_person_id: str | None
    station: StationView | None
    side: str | None
    result: dict[str, Any]
    state_changed: bool
    is_squat_station: bool


@runtime_checkable
class IdentityResolver(Protocol):
    """
    Resolve one frame centroid to physical and logical IDs.

    Expected error:
    - Raises RuntimeError when no identity can be allocated/resolved.
      `process_person(...)` treats this as a skip (non-fatal).
    """

    def resolve(self, centroid: np.ndarray) -> IdentityResolution:
        ...


@runtime_checkable
class StationProvider(Protocol):
    """Provides current station assignment for a logical session person."""

    def get_station(self, session_person_id: str) -> StationView:
        ...


@runtime_checkable
class Detector(Protocol):
    """Exercise detector for one logical session person."""

    def analyze(self, person_kp: np.ndarray) -> Mapping[str, Any]:
        ...


@runtime_checkable
class DetectorProvider(Protocol):
    """Returns detector instances per logical session person."""

    def get(self, session_person_id: str) -> Detector:
        ...


class SessionSyncFn(Protocol):
    """
    Sync function for canonical session state.

    Any exception raised here is propagated as fatal for the current frame.
    """

    def __call__(
        self,
        *,
        session_state: SessionState,
        session_person_id: str,
        station_id: str,
        result: Mapping[str, Any],
        is_squat_station: bool,
    ) -> bool:
        ...


class SquatFeedbackRenderer(Protocol):
    """Optional hook to render feedback/overlays for squat frames."""

    def __call__(
        self,
        *,
        person_kp: np.ndarray,
        side: str,
        result: Mapping[str, Any],
    ) -> None:
        ...


__all__ = [
    "StationView",
    "IdentityResolution",
    "ProcessPersonOutput",
    "IdentityResolver",
    "StationProvider",
    "Detector",
    "DetectorProvider",
    "SessionSyncFn",
    "SquatFeedbackRenderer",
]
