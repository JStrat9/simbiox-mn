import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.errors.error_normalizer import (
    build_errors_v2_from_codes,
    canonicalize_errors_v2,
    normalize_detector_errors,
)


class ErrorNormalizerTests(unittest.TestCase):
    def test_normalize_detector_errors_maps_text_to_stable_codes(self):
        normalized = normalize_detector_errors(
            [
                "Rodillas adelantadas",
                "No bajas lo suficiente",
                "Rodillas adelantadas",
            ]
        )

        self.assertEqual(
            normalized,
            [
                {
                    "code": "DEPTH_INSUFFICIENT",
                    "message_key": "error.squat.depth_insufficient",
                    "severity": "warning",
                    "metadata": {},
                },
                {
                    "code": "KNEE_FORWARD",
                    "message_key": "error.squat.knee_forward",
                    "severity": "warning",
                    "metadata": {},
                },
            ],
        )

    def test_canonicalize_errors_v2_dedupes_and_normalizes_severity(self):
        normalized = canonicalize_errors_v2(
            [
                {
                    "code": "KNEE_FORWARD",
                    "severity": "critical",
                    "metadata": {"frames": 3},
                },
                {
                    "code": "KNEE_FORWARD",
                    "severity": "critical",
                    "metadata": {"frames": 3},
                },
                {
                    "code": "DEPTH_INSUFFICIENT",
                    "severity": "not-valid",
                    "metadata": {},
                },
            ]
        )

        self.assertEqual(
            normalized,
            [
                {
                    "code": "DEPTH_INSUFFICIENT",
                    "message_key": "error.squat.depth_insufficient",
                    "severity": "warning",
                    "metadata": {},
                },
                {
                    "code": "KNEE_FORWARD",
                    "message_key": "error.squat.knee_forward",
                    "severity": "critical",
                    "metadata": {"frames": 3},
                },
            ],
        )

    def test_build_errors_v2_from_codes_handles_unknowns(self):
        normalized = build_errors_v2_from_codes(["DEPTH_INSUFFICIENT", "NO_EXISTE"])

        self.assertEqual(
            normalized,
            [
                {
                    "code": "DEPTH_INSUFFICIENT",
                    "message_key": "error.squat.depth_insufficient",
                    "severity": "warning",
                    "metadata": {},
                },
                {
                    "code": "UNKNOWN_ERROR",
                    "message_key": "error.generic.unknown",
                    "severity": "warning",
                    "metadata": {"raw_error": "NO_EXISTE"},
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
