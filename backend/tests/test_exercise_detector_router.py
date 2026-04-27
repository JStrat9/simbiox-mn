import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from detectors.exercise_detector_router import ExerciseDetectorRouter


class ExerciseDetectorRouterTests(unittest.TestCase):
    def test_get_returns_same_detector_when_exercise_does_not_change(self):
        router = ExerciseDetectorRouter(max_clients=1)
        first = router.get("athlete_1", "squat")
        second = router.get("athlete_1", "squat")
        self.assertIs(first, second)

    def test_switching_exercise_resets_previous_detector(self):
        router = ExerciseDetectorRouter(max_clients=1)

        squat_detector = router.get("athlete_1", "squat")
        squat_detector.confirmed_error_dicts["BACK_ROUNDED"] = {
            "code": "BACK_ROUNDED",
            "message_key": "error.squat.back_rounded",
            "severity": "warning",
            "metadata": {"hip_angle": 40.0},
        }

        router.get("athlete_1", "renegade_row")
        squat_detector_after_switch = router.get("athlete_1", "squat")

        self.assertIsNot(squat_detector, squat_detector_after_switch)
        self.assertEqual(squat_detector_after_switch.confirmed_error_dicts, {})

    def test_clear_reviewed_errors_keeps_detector_progress_but_clears_confirmed(self):
        router = ExerciseDetectorRouter(max_clients=1)
        squat_detector = router.get("athlete_1", "squat")
        squat_detector.reps = 5
        squat_detector.confirmed_error_dicts["BACK_ROUNDED"] = {
            "code": "BACK_ROUNDED",
            "message_key": "error.squat.back_rounded",
            "severity": "warning",
            "metadata": {"hip_angle": 40.0},
        }
        squat_detector.error_rep_count["BACK_ROUNDED"] = 2
        squat_detector.current_rep_errors["BACK_ROUNDED"] = 1
        squat_detector.current_rep_error_dicts["BACK_ROUNDED"] = {
            "code": "BACK_ROUNDED",
            "message_key": "error.squat.back_rounded",
            "severity": "warning",
            "metadata": {"hip_angle": 41.0},
        }
        squat_detector.squat_errors_sent.add("BACK_ROUNDED")

        router.clear_reviewed_errors("athlete_1")
        same_detector = router.get("athlete_1", "squat")

        self.assertIs(same_detector, squat_detector)
        self.assertEqual(same_detector.reps, 5)
        self.assertEqual(same_detector.confirmed_error_dicts, {})
        self.assertNotIn("BACK_ROUNDED", same_detector.error_rep_count)
        self.assertNotIn("BACK_ROUNDED", same_detector.current_rep_errors)
        self.assertNotIn("BACK_ROUNDED", same_detector.current_rep_error_dicts)
        self.assertNotIn("BACK_ROUNDED", same_detector.squat_errors_sent)


if __name__ == "__main__":
    unittest.main()
