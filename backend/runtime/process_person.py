from utils.deprecation import warn_legacy_module

warn_legacy_module(
    module_name="runtime.process_person",
    replacement="application.use_cases.process_person_uc",
)

from application.use_cases.process_person_uc import get_centroid, process_person

__all__ = ["get_centroid", "process_person"]
