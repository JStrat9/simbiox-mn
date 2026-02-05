# rotation.py

from session.session_state import SessionState

def rotate_stations(session: SessionState):
    order = session.station_order
    new_assignments = {}

    for athlete_id, station_id in session.assignments.items():
        idx = order.index(station_id)
        next_station = order[(idx + 1) % len(order)]
        new_assignments[athlete_id] = next_station

    session.assignments = new_assignments
    session.rotation_index += 1

    return new_assignments 