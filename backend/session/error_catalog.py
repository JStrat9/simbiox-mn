from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="session.error_catalog",
    replacement="domain.errors.error_catalog",
)

from domain.errors.error_catalog import (
    DETECTOR_TEXT_TO_ERROR_CODE,
    KNOWN_ERRORS,
    ErrorSeverity,
    ErrorSpec,
    default_message_key_for_code,
    default_severity_for_code,
    normalize_error_code,
)

__all__ = [
    "ErrorSeverity",
    "ErrorSpec",
    "KNOWN_ERRORS",
    "DETECTOR_TEXT_TO_ERROR_CODE",
    "normalize_error_code",
    "default_severity_for_code",
    "default_message_key_for_code",
]
