from __future__ import annotations

from typing import Final, Literal, TypedDict

ErrorSeverity = Literal["info", "warning", "critical"]


class ErrorSpec(TypedDict):
    severity: ErrorSeverity
    message_key: str


KNOWN_ERRORS: Final[dict[str, ErrorSpec]] = {
    "DEPTH_INSUFFICIENT": {
        "severity": "warning",
        "message_key": "error.squat.depth_insufficient",
    },
    "DEPTH_EXCESSIVE": {
        "severity": "warning",
        "message_key": "error.squat.depth_excessive",
    },
    "BACK_ROUNDED": {
        "severity": "warning",
        "message_key": "error.squat.back_rounded",
    },
    "KNEE_FORWARD": {
        "severity": "warning",
        "message_key": "error.squat.knee_forward",
    },
    "RANGE_INSUFFICIENT": {
        "severity": "warning",
        "message_key": "error.exercise.range_insufficient",
    },
    "ELBOW_OVERFLEXION": {
        "severity": "warning",
        "message_key": "error.exercise.elbow_overflexion",
    },
    "HIP_SAGGING": {
        "severity": "warning",
        "message_key": "error.exercise.hip_sagging",
    },
    "HIP_HIGH": {
        "severity": "warning",
        "message_key": "error.exercise.hip_high",
    },
    "UNKNOWN_ERROR": {
        "severity": "warning",
        "message_key": "error.generic.unknown",
    },
}


DETECTOR_TEXT_TO_ERROR_CODE: Final[dict[str, str]] = {
    "no bajas lo suficiente": "DEPTH_INSUFFICIENT",
    "baja demasiado": "DEPTH_EXCESSIVE",
    "espalda encorvada": "BACK_ROUNDED",
    "rodillas adelantadas": "KNEE_FORWARD",
}


def normalize_error_code(raw_code: str) -> str:
    raw = (raw_code or "").strip()
    if not raw:
        return "UNKNOWN_ERROR"

    normalized_candidate = raw.upper().replace(" ", "_")
    if normalized_candidate in KNOWN_ERRORS:
        return normalized_candidate

    mapped = DETECTOR_TEXT_TO_ERROR_CODE.get(raw.lower())
    if mapped:
        return mapped

    return "UNKNOWN_ERROR"


def default_severity_for_code(code: str) -> ErrorSeverity:
    return KNOWN_ERRORS.get(code, KNOWN_ERRORS["UNKNOWN_ERROR"])["severity"]


def default_message_key_for_code(code: str) -> str:
    return KNOWN_ERRORS.get(code, KNOWN_ERRORS["UNKNOWN_ERROR"])["message_key"]
