# feedback/feedback_mapper.py

from typing import Dict, List, Optional

def map_squat_event(client_id: str, result: Dict, prev_errors: Optional[List[str]] = None) -> List[Dict]:
    """
    Convierte output de SquatDetector en lista de eventos listos para emitir por WS.
    
    Args:
        client_id: ID del cliente
        result: salida de SquatDetector.analyze()
        prev_errors: errores previos para detectar duplicados

    Returns:
        Lista de eventos: cada evento es dict con `type` y payload mínimo
    """

    events = []
    prev_errors = prev_errors or []

    # REP_UPDATE
    events.append({
        "type": "REP_UPDATE",
        "clientId": client_id,
        "reps": result.get("reps", 0)
    })

    # POSE_ERROR
    current_errors = result.get("errors", [])
    new_errors = [e for e in current_errors if e not in prev_errors]

    for err in new_errors:
        events.append({
            "type": "POSE_ERROR",
            "clientId": client_id,
            "exercise": result.get("exercise", "unknown"),
            "errorCode": err,
        })

    return events