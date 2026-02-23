from __future__ import annotations

from typing import Final, Literal, TypedDict

ErrorSeverity = Literal["info", "warning", "critical"]


class ErrorSpec(TypedDict):
    severity: ErrorSeverity


KNOWN_ERRORS: Final[dict[str, ErrorSpec]] = {
    "DEPTH_INSUFFICIENT": {"severity": "warning"},
    "DEPTH_EXCESSIVE": {"severity": "warning"},
    "BACK_ROUNDED": {"severity": "warning"},
    "KNEE_FORWARD": {"severity": "warning"},
    "UNKNOWN_ERROR": {"severity": "warning"},
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
