# rotation.py

import time

from session.session_state import SessionState


def rotate_stations(session: SessionState):
    order = session.station_order
    new_assignments = {}

    for athlete_id, station_id in session.assignments.items():
        idx = order.index(station_id)
        next_station = order[(idx + 1) % len(order)]
        new_assignments[athlete_id] = next_station

    if new_assignments != session.assignments:
        session.assignments = new_assignments
        session.rotation_index += 1
        session.updated_at = int(time.time())
        session.version += 1

    return session.assignments
