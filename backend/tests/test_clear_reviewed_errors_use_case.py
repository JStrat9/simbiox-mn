import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from application.use_cases.clear_reviewed_errors_uc import (
    clear_reviewed_errors_use_case,
)
from domain.errors.error_normalizer import build_errors_v2_from_codes
from domain.session.session_state import SessionState


class _RuntimeReviewedErrorsSyncSpy:
    def __init__(self):
        self.calls: list[str] = []

    def clear(self, session_person_id: str) -> None:
        self.calls.append(session_person_id)


class ClearReviewedErrorsUseCaseTests(unittest.TestCase):
    def test_clears_session_errors_syncs_runtime_and_returns_snapshot(self):
        state = SessionState()
        runtime_sync = _RuntimeReviewedErrorsSyncSpy()
        state.set_errors_v2(
            "athlete_1",
            build_errors_v2_from_codes(["BACK_ROUNDED"]),
            increment_version=False,
        )
        state.set_errors_v2(
            "athlete_2",
            build_errors_v2_from_codes(["KNEE_FORWARD"]),
            increment_version=False,
        )

        event = clear_reviewed_errors_use_case(
            session_state=state,
            runtime_reviewed_errors_sync=runtime_sync,
        )

        self.assertEqual(event["type"], "SESSION_UPDATE")
        self.assertGreaterEqual(state.version, 1)
        self.assertEqual(state.errors["athlete_1"], [])
        self.assertEqual(state.errors_v2["athlete_1"], [])
        self.assertEqual(state.errors["athlete_2"], [])
        self.assertEqual(state.errors_v2["athlete_2"], [])
        self.assertEqual(len(runtime_sync.calls), len(state.assignments))
        self.assertEqual(set(runtime_sync.calls), set(state.assignments.keys()))

    def test_works_without_runtime_sync(self):
        state = SessionState()
        state.set_errors_v2(
            "athlete_1",
            build_errors_v2_from_codes(["BACK_ROUNDED"]),
            increment_version=False,
        )

        event = clear_reviewed_errors_use_case(session_state=state)

        self.assertEqual(event["type"], "SESSION_UPDATE")
        self.assertEqual(state.errors_v2["athlete_1"], [])


if __name__ == "__main__":
    unittest.main()
