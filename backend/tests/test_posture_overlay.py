import sys
import types
import importlib
import numpy as np

# --- Create lightweight fake modules BEFORE importing project modules --- #
# Provide utils.geometry.angle so detectors.posture_utils can import it
fake_geom = types.ModuleType("utils.geometry")
fake_geom.angle = lambda a, b, c: 90  # force angle == 90 as requested
fake_geom.calculate_angle = fake_geom.angle
fake_geom.angle_from_arrays = fake_geom.angle
sys.modules["utils.geometry"] = fake_geom

# Provide communication.websocket_server.send_error_threadsafe to capture calls
_sent = []
fake_ws = types.ModuleType("communication.websocket_server")
def _send_error_threadsafe(data):
    _sent.append(data)
fake_ws.send_error_threadsafe = _send_error_threadsafe
sys.modules["communication.websocket_server"] = fake_ws

# Ensure fresh import (in case tests run in same process)
for m in ("detectors.posture_utils", "video.posture_overlay"):
    if m in sys.modules:
        del sys.modules[m]

# --- Now import the real functions to test --- #
from detectors.posture_utils import knee_angle_left, knee_angle_right
from video.posture_overlay import analyze_and_draw

# --- Simulated landmarks (same shape/keys expected by posture_utils) --- #
kp = [(0.0, 0.0, 0.0)] * 17
# left side
kp[11] = (0.5, 0.5, 0.9)   # left_hip
kp[13] = (0.5, 0.7, 0.9)   # left_knee
kp[15] = (0.5, 0.9, 0.9)   # left_ankle
# right side
kp[12] = (0.6, 0.5, 0.9)   # right_hip
kp[14] = (0.6, 0.7, 0.9)   # right_knee
kp[16] = (0.6, 0.9, 0.9)   # right_ankle

# analyze_and_draw expects landmarks as a list of people -> pass [kp]
mock_landmarks = [kp]

# --- Minimal mock detector required by analyze_and_draw --- #
class MockDetector:
    def __init__(self):
        self.last_feedback_sent = None
        self.squat_stage = "down"
    def analyze(self, landmarks):
        # angles use mocked geometry.angle => knee angles will be 90
         return {
            "angles": {"knee": 90, "hip": 120, "elbow": 90, "ankle": 90},  # <-- added "ankle"
            "joints": {"knee": (0.5, 0.7), "hip": (0.5, 0.5), "elbow": (0.5, 0.3), "ankle": (0.5, 0.9)},
            "minmax": {"min_knee": 70, "max_knee": 130, "min_hip": 60, "max_hip": 140, "min_elbow": 40, "max_elbow": 100},
            "feedback": "Bajaste poco",
            "counter": 3,
            "detection_active": True
        }

# --- Test execution --- #
def test_posture_pipeline_minimal():
    # verify knee angle helpers execute (they use mocked angle -> 90)
    left = knee_angle_left(mock_landmarks[0])
    right = knee_angle_right(mock_landmarks[0])
    assert left == 90
    assert right == 90

    # prepare a fake frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det = MockDetector()

    # call analyze_and_draw (should not raise) and return an image
    out = analyze_and_draw(frame.copy(), frame_width=640, frame_height=480, detector=det, landmarks=mock_landmarks, loop=None, client_id="test-client")
    assert out is not None
    assert out.shape == frame.shape

    # verify send_error_threadsafe was invoked with expected feedback (mock captured it)
    assert len(_sent) >= 1
    found = False
    for s in _sent:
        if s.get("feedback") == "Bajaste poco" and s.get("clientId") == "test-client":
            found = True
            break
    assert found, f"Expected send_error_threadsafe to be called with feedback 'Bajaste poco', captured: {_sent}"

if __name__ == "__main__":
    test_posture_pipeline_minimal()
    print("✅ test_posture_pipeline_minimal passed")