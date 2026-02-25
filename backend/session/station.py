from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="session.station",
    replacement="interfaces.runtime.station",
)

from interfaces.runtime.station import Station

__all__ = ["Station"]
    
