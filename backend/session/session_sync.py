from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="session.session_sync",
    replacement="domain.session.sync_policy",
)

from domain.session.sync_policy import sync_session_state_for_person

__all__ = ["sync_session_state_for_person"]
