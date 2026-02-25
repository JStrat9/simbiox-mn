import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from interfaces.runtime.session_person_manager import (
    SessionPersonManager as CanonicalSessionPersonManager,
)
from interfaces.runtime.station import Station as CanonicalStation
from session.session_person_manager import SessionPersonManager as ShimSessionPersonManager
from session.station import Station as ShimStation


class SessionPersonManagerShimsTests(unittest.TestCase):
    def test_session_person_manager_shim_points_to_interfaces_runtime(self):
        self.assertIs(ShimSessionPersonManager, CanonicalSessionPersonManager)

    def test_station_shim_points_to_interfaces_runtime(self):
        self.assertIs(ShimStation, CanonicalStation)


if __name__ == "__main__":
    unittest.main()
