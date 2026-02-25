from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="session.rotation",
    replacement="domain.session.rotation_policy",
)

from domain.session.rotation_policy import rotate_stations

__all__ = ["rotate_stations"]
