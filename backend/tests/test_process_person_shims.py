import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from application.ports.process_person_ports import (
    DetectorProvider as AppDetectorProvider,
    IdentityResolution as AppIdentityResolution,
    IdentityResolver as AppIdentityResolver,
    ProcessPersonOutput as AppProcessPersonOutput,
    SessionSyncFn as AppSessionSyncFn,
    StationProvider as AppStationProvider,
)
from application.use_cases.process_person_uc import (
    get_centroid as app_get_centroid,
    process_person as app_process_person,
)
from runtime.contracts import (
    DetectorProvider as ShimDetectorProvider,
    IdentityResolution as ShimIdentityResolution,
    IdentityResolver as ShimIdentityResolver,
    ProcessPersonOutput as ShimProcessPersonOutput,
    SessionSyncFn as ShimSessionSyncFn,
    StationProvider as ShimStationProvider,
)
from runtime.process_person import (
    get_centroid as shim_get_centroid,
    process_person as shim_process_person,
)


class ProcessPersonShimsTests(unittest.TestCase):
    def test_runtime_process_person_shim_points_to_application_use_case(self):
        self.assertIs(shim_process_person, app_process_person)
        self.assertIs(shim_get_centroid, app_get_centroid)

    def test_runtime_contract_shim_points_to_application_ports(self):
        self.assertIs(ShimIdentityResolution, AppIdentityResolution)
        self.assertIs(ShimProcessPersonOutput, AppProcessPersonOutput)
        self.assertIs(ShimIdentityResolver, AppIdentityResolver)
        self.assertIs(ShimStationProvider, AppStationProvider)
        self.assertIs(ShimDetectorProvider, AppDetectorProvider)
        self.assertIs(ShimSessionSyncFn, AppSessionSyncFn)


if __name__ == "__main__":
    unittest.main()
