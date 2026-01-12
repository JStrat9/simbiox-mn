# session/session_person_manager.py

import time
import numpy as np
from typing import Dict, Optional
from enum import Enum

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

        self.current_station: Optional[str] = None
        self.active: bool = True

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

            self.persons: Dict[str, SessionPerson] = {}
            self.next_person_id = 1

    def _update_state(self, now: float):
        for person in self.persons.values():
            dt = now - person.last_seen_ts

            if dt <= self.t_active:
                person.state = PersonState.ACTIVE
            elif dt <= self.t_lost:
                person.state = PersonState.LOST
            else:
                person.state = PersonState.INACTIVE

    # ------------ public API ------------
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
            if dt > self.reassignment_timeout:
                continue
            if person.last_client_centroid is None:
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
        Create a new session person
        """

        if len(self.persons) >= self.max_persons:
            raise RuntimeError("Maximum number of persons reached")
        
        pid = f"person{self.next_person_id}"
        self.next_person_id += 1

        person = SessionPerson(pid)
        person.last_client_id = client_id
        person.last_client_centroid = centroid
        person.last_seen_ts = time.time()
        person.state = PersonState.ACTIVE

        self.persons[pid] = person

        return person