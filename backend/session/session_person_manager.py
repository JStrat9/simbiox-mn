from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="session.session_person_manager",
    replacement="interfaces.runtime.session_person_manager",
)

from interfaces.runtime.session_person_manager import (
    ALLOWED_IDS,
    PersonState,
    SessionPerson,
    SessionPersonManager,
)

__all__ = [
    "ALLOWED_IDS",
    "PersonState",
    "SessionPerson",
    "SessionPersonManager",
]
