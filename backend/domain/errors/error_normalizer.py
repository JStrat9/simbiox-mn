from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, TypedDict

from domain.errors.error_catalog import (
    ErrorSeverity,
    default_message_key_for_code,
    default_severity_for_code,
    normalize_error_code,
)


class ErrorV2(TypedDict):
    code: str
    message_key: str
    severity: ErrorSeverity
    metadata: dict[str, Any]


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def _sanitize_metadata(raw_metadata: Any) -> dict[str, Any]:
    if not isinstance(raw_metadata, Mapping):
        return {}

    encoded = _canonical_json(dict(raw_metadata))
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        return {}
    return decoded


def _normalize_severity(code: str, raw_severity: Any) -> ErrorSeverity:
    if raw_severity in ("info", "warning", "critical"):
        return raw_severity
    return default_severity_for_code(code)


def _normalize_error_item(raw_error: Any) -> ErrorV2:
    if isinstance(raw_error, Mapping):
        raw_code = str(raw_error.get("code", ""))
        code = normalize_error_code(raw_code)
        raw_message_key = str(raw_error.get("message_key", "")).strip()
        message_key = raw_message_key or default_message_key_for_code(code)
        severity = _normalize_severity(code, raw_error.get("severity"))
        metadata = _sanitize_metadata(raw_error.get("metadata", {}))

        if code == "UNKNOWN_ERROR" and raw_code and "raw_error" not in metadata:
            metadata["raw_error"] = raw_code

        return {
            "code": code,
            "message_key": message_key,
            "severity": severity,
            "metadata": metadata,
        }

    raw_text = str(raw_error or "")
    code = normalize_error_code(raw_text)
    message_key = default_message_key_for_code(code)
    severity = default_severity_for_code(code)
    metadata: dict[str, Any] = {}
    if code == "UNKNOWN_ERROR" and raw_text:
        metadata["raw_error"] = raw_text

    return {
        "code": code,
        "message_key": message_key,
        "severity": severity,
        "metadata": metadata,
    }


def canonicalize_errors_v2(errors_v2: Iterable[Any] | None) -> list[ErrorV2]:
    if not errors_v2:
        return []

    deduped: dict[tuple[str, str, str], ErrorV2] = {}
    for raw_error in errors_v2:
        normalized = _normalize_error_item(raw_error)
        key = (
            normalized["code"],
            normalized["message_key"],
            normalized["severity"],
            _canonical_json(normalized["metadata"]),
        )
        deduped[key] = normalized

    return [
        deduped[key]
        for key in sorted(
            deduped.keys(),
            key=lambda item: (item[0], item[1], item[2], item[3]),
        )
    ]


def error_codes_from_errors_v2(errors_v2: Iterable[Mapping[str, Any]] | None) -> list[str]:
    return [entry["code"] for entry in canonicalize_errors_v2(errors_v2)]


def build_errors_v2_from_codes(error_codes: Iterable[str] | None) -> list[ErrorV2]:
    return canonicalize_errors_v2(
        [{"code": code, "metadata": {}} for code in (error_codes or [])]
    )


def normalize_detector_errors(raw_errors: Iterable[Any] | None) -> list[ErrorV2]:
    return canonicalize_errors_v2(raw_errors)
