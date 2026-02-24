import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.errors.error_catalog import normalize_error_code as domain_normalize_error_code
from domain.errors.error_normalizer import (
    canonicalize_errors_v2 as domain_canonicalize_errors_v2,
)
from domain.session.rotation_policy import rotate_stations as domain_rotate_stations
from domain.session.session_state import SessionState as DomainSessionState
from domain.session.sync_policy import (
    sync_session_state_for_person as domain_sync_session_state_for_person,
)
from session.error_catalog import normalize_error_code as shim_normalize_error_code
from session.error_normalizer import canonicalize_errors_v2 as shim_canonicalize_errors_v2
from session.rotation import rotate_stations as shim_rotate_stations
from session.session_state import SessionState as ShimSessionState
from session.session_sync import (
    sync_session_state_for_person as shim_sync_session_state_for_person,
)


class DomainShimsTests(unittest.TestCase):
    def test_session_state_shim_points_to_domain_class(self):
        self.assertIs(ShimSessionState, DomainSessionState)

    def test_rotation_shim_points_to_domain_policy(self):
        self.assertIs(shim_rotate_stations, domain_rotate_stations)

    def test_session_sync_shim_points_to_domain_policy(self):
        self.assertIs(
            shim_sync_session_state_for_person,
            domain_sync_session_state_for_person,
        )

    def test_error_catalog_shim_points_to_domain_function(self):
        self.assertIs(shim_normalize_error_code, domain_normalize_error_code)

    def test_error_normalizer_shim_points_to_domain_function(self):
        self.assertIs(shim_canonicalize_errors_v2, domain_canonicalize_errors_v2)


if __name__ == "__main__":
    unittest.main()
