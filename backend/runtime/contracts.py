from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="runtime.contracts",
    replacement="application.ports.process_person_ports",
)

from application.ports.process_person_ports import (
    Detector,
    DetectorProvider,
    IdentityResolution,
    IdentityResolver,
    ProcessPersonOutput,
    SessionSyncFn,
    SquatFeedbackRenderer,
    StationProvider,
    StationView,
)

__all__ = [
    "StationView",
    "IdentityResolution",
    "ProcessPersonOutput",
    "IdentityResolver",
    "StationProvider",
    "Detector",
    "DetectorProvider",
    "SessionSyncFn",
    "SquatFeedbackRenderer",
]
