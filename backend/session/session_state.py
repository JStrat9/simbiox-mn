from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="session.session_state",
    replacement="domain.session.session_state",
)

from domain.session.session_state import SessionState

__all__ = ["SessionState"]
