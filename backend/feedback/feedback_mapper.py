# feedback/feedback_mapper.py

from typing import Optional, Dict

def map_squat_feedback(result: Dict) -> Dict:
    """
    Traduce el output de SquatDetector a feedback simple para UI.
    Devuelve solo reps y un error activo.
    """

    if not result or not result.get("valid"):
        return  {
            "reps": None,
            "error": "no_pose_detected"
        }
    
    reps = result.get("reps", 0)

    errors = result.get("errors", [])
    active_error: Optional[str] = errors[0] if errors else None

    return {
        "reps": reps,
        "error": active_error
    }