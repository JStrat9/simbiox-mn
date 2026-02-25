import time
from enum import Enum
from typing import Dict, Optional

import numpy as np

from domain.session.session_state import SessionState
from interfaces.runtime.station import Station
from tracking.tracker_iou import CentroidTracker

ALLOWED_IDS = [f"athlete_{i}" for i in range(1, 7)]


class PersonState(Enum):
    ACTIVE = "active"
    LOST = "lost"
    INACTIVE = "inactive"


class SessionPerson:
    def __init__(self, session_person_id: str):
        self.session_person_id = session_person_id
        self.last_client_id: Optional[str] = None
        self.last_client_centroid: Optional[np.ndarray] = None
        self.last_seen_ts: float = time.time()
        self.state: PersonState = PersonState.ACTIVE
        self.active: bool = True
        self.current_station_id: str | None = None
        self.session_state: SessionState | None = None


class SessionPersonManager:
    def __init__(
        self,
        max_persons: int,
        reassignment_timeout: float = 2.0,
        t_active: float = 0.8,
        t_lost: float = 2.5,
        distance_threshold: float = 120.0,
    ):
        self.max_persons = max_persons
        self.t_active = t_active
        self.reassignment_timeout = reassignment_timeout
        self.t_lost = t_lost
        self.distance_threshold = distance_threshold
        self.session_state: SessionState | None = None

        self.persons: Dict[str, SessionPerson] = {}
        self.client_tracker = CentroidTracker(
            max_clients=max_persons,
            distance_threshold=distance_threshold,
        )

    # ----------------- Person State Management -----------------
    def _update_state(self, now: float):
        for person in self.persons.values():
            dt = now - person.last_seen_ts
            if dt <= self.t_active:
                person.state = PersonState.ACTIVE
            elif dt <= self.t_lost:
                person.state = PersonState.LOST
            else:
                person.state = PersonState.INACTIVE

    # ------------ Public API ------------
    def resolve_identity(self, centroid: np.ndarray) -> tuple[str, str]:
        """
        Resolve physical and logical identity for one detection.

        Returns:
            (client_id, session_person_id)

        Raises:
            RuntimeError if no client_id or athlete_id can be allocated.
        """
        client_id = self.client_tracker.get_client_id(centroid)
        session_person_id = self.resolve_person(client_id, centroid)
        return client_id, session_person_id

    def release_missing_client_ids(self, current_ids: set[str]):
        """
        Release physical client IDs not seen in current frame.
        """
        self.client_tracker.release_missing(current_ids)

    def resolve_person(self, client_id: str, centroid: np.ndarray) -> str:
        """
        Decide wich session_person_id does this client_id belong to
        """

        now = time.time()
        self._update_state(now)

        # Try reassignation
        person = self._find_reassignable_person(centroid, now)
        if person:
            old_client_id = person.last_client_id
            person.last_client_id = client_id
            person.last_client_centroid = centroid
            person.last_seen_ts = now
            person.state = PersonState.ACTIVE

            # --- DEBUG reasignation ---
            if old_client_id and old_client_id != client_id:
                print(
                    f"[SESSION][REASSIGN] "
                    f"{old_client_id} -> {client_id} "
                    f"on {person.session_person_id}"
                )
            return person.session_person_id

        # Try to create a new person
        person = self._create_new_person(client_id, centroid)
        return person.session_person_id

    def update_seen(self, session_person_id: str, centroid: np.ndarray):
        """
        Update the last seen timestamp and centroid of a session person
        """
        person = self.persons.get(session_person_id)
        if not person:
            return

        person.last_client_centroid = centroid
        person.last_seen_ts = time.time()

    def _find_reassignable_person(
        self, centroid: np.ndarray, now: float
    ) -> Optional[SessionPerson]:
        """
        Find a reassignable person
        """
        best_person = None
        best_dist = float("inf")

        for person in self.persons.values():
            dt = now - person.last_seen_ts
            if dt > self.reassignment_timeout or person.last_client_centroid is None:
                continue

            dist = np.linalg.norm(centroid - person.last_client_centroid)
            print(
                f"[TRACK] reassign check | "
                f"person:{person.session_person_id} "
                f"dt={dt:.2f} "
                f"dist={dist:.1f} "
                f"client_id={centroid}"
            )
            if dist < self.distance_threshold and dist < best_dist:
                best_dist = dist
                best_person = person

        return best_person

    def _create_new_person(self, client_id: str, centroid: np.ndarray) -> SessionPerson:
        """
        Create a new session person using allowed athlete IDs and
        link them to their assigned station from session_state.
        """

        if len(self.persons) >= self.max_persons:
            raise RuntimeError("Maximum number of persons reached")

        if not self.session_state:
            raise RuntimeError("SessionState not set in SessionPersonManager")

        # Buscar un ID libre
        used_ids = {
            p.session_person_id
            for p in self.persons.values()
            if p.state != PersonState.INACTIVE
        }
        available_ids = [aid for aid in ALLOWED_IDS if aid not in used_ids]

        if not available_ids:
            raise RuntimeError("No available athlete IDs")

        pid = available_ids[0]  # asignar el primer disponible

        person = SessionPerson(pid)
        person.last_client_id = client_id
        person.last_client_centroid = centroid
        person.last_seen_ts = time.time()
        person.state = PersonState.ACTIVE
        person.current_station_id = self.session_state.assignments.get(pid, "station1")
        self.persons[pid] = person
        return person

    def assign_station(self, session_person_id: str, station_id: str):
        """
        Assign a station to a session person runtime view.
        """
        person = self.persons.get(session_person_id)
        if not person:
            return
        person.current_station_id = station_id

    def get_station(self, session_person_id: str) -> Station:
        """Return the Station object for a session person"""
        person = self.persons.get(session_person_id)
        if not person:
            # fallback dummy
            return Station(station_id="station1", exercise="squat", reps=0)

        station_id = person.current_station_id
        if not station_id and self.session_state:
            station_id = self.session_state.assignments.get(session_person_id, "station1")

        exercise = (
            self.session_state.station_map.get(station_id, "squat")
            if self.session_state
            else "squat"
        )
        # Optional: use session_state for reps tracking, or default to 0
        reps = 0
        if self.session_state and session_person_id in self.session_state.reps:
            reps = self.session_state.reps[session_person_id]

        return Station(station_id=station_id, exercise=exercise, reps=reps)


__all__ = [
    "ALLOWED_IDS",
    "PersonState",
    "SessionPerson",
    "SessionPersonManager",
]
