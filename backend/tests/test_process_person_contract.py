import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from runtime.contracts import IdentityResolution
from runtime.process_person import process_person
from session.session_state import SessionState
from session.session_sync import sync_session_state_for_person
from session.station import Station


def _fake_person_kp() -> np.ndarray:
    keypoints = np.zeros((17, 3), dtype=float)
    keypoints[:, 2] = 0.9
    keypoints[:, 0] = np.linspace(0.1, 0.9, 17)
    keypoints[:, 1] = np.linspace(0.2, 0.8, 17)
    return keypoints


class _ResolverA:
    def resolve(self, centroid: np.ndarray) -> IdentityResolution:
        return IdentityResolution(client_id="client-A", session_person_id="athlete_1")


class _ResolverB:
    def resolve(self, centroid: np.ndarray) -> IdentityResolution:
        # Different internal strategy / physical ID, same logical identity.
        _ = float(np.linalg.norm(centroid))
        return IdentityResolution(client_id="client-B", session_person_id="athlete_1")


class _FailingResolver:
    def resolve(self, centroid: np.ndarray) -> IdentityResolution:
        raise RuntimeError("no available IDs")


class _StationProvider:
    def __init__(self, exercise: str = "squat"):
        self.exercise = exercise

    def get_station(self, session_person_id: str) -> Station:
        return Station(station_id="station1", exercise=self.exercise, reps=0)


class _Detector:
    def analyze(self, person_kp: np.ndarray):
        return {
            "valid": True,
            "reps": 2,
            "errors": ["DEPTH_INSUFFICIENT"],
            "angles": {"knee": 72},
        }


class _DetectorProvider:
    def get(self, session_person_id: str):
        return _Detector()


class _FailIfCalledProvider:
    def get_station(self, session_person_id: str) -> Station:
        raise AssertionError("station provider should not be called")

    def get(self, session_person_id: str):
        raise AssertionError("detector provider should not be called")


class ProcessPersonContractTests(unittest.TestCase):
    def _run(self, resolver, state: SessionState):
        return process_person(
            _fake_person_kp(),
            session_state=state,
            identity_resolver=resolver,
            station_provider=_StationProvider(exercise="squat"),
            detector_provider=_DetectorProvider(),
            sync_state_fn=sync_session_state_for_person,
            on_squat_feedback=None,
        )

    @staticmethod
    def _functional_projection(output) -> dict:
        return {
            "skipped": output.skipped,
            "session_person_id": output.session_person_id,
            "station_id": output.station.station_id if output.station else None,
            "exercise": output.station.exercise if output.station else None,
            "result": output.result,
            "state_changed": output.state_changed,
            "is_squat_station": output.is_squat_station,
            "side": output.side,
        }

    def test_resolver_is_replaceable_without_breaking_functional_output(self):
        state_a = SessionState()
        state_b = SessionState()

        output_a = self._run(_ResolverA(), state_a)
        output_b = self._run(_ResolverB(), state_b)

        self.assertNotEqual(output_a.client_id, output_b.client_id)
        self.assertEqual(
            self._functional_projection(output_a),
            self._functional_projection(output_b),
        )
        self.assertEqual(state_a.reps["athlete_1"], state_b.reps["athlete_1"])
        self.assertEqual(state_a.errors["athlete_1"], state_b.errors["athlete_1"])
        self.assertEqual(state_a.version, state_b.version)

    def test_runtime_error_from_resolver_is_reported_as_skip(self):
        state = SessionState()

        output = process_person(
            _fake_person_kp(),
            session_state=state,
            identity_resolver=_FailingResolver(),
            station_provider=_FailIfCalledProvider(),
            detector_provider=_FailIfCalledProvider(),
            sync_state_fn=sync_session_state_for_person,
            on_squat_feedback=None,
        )

        self.assertTrue(output.skipped)
        self.assertEqual(output.skip_reason, "no available IDs")
        self.assertIsNone(output.client_id)
        self.assertIsNone(output.session_person_id)
        self.assertFalse(output.state_changed)
        self.assertEqual(state.version, 0)


if __name__ == "__main__":
    unittest.main()
