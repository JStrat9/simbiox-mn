import sys
import types
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if "dotenv" not in sys.modules:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda: None)

import main as backend_main


class MainBootstrapTests(unittest.TestCase):
    def test_bootstrap_returns_error_if_ws_is_not_ready(self):
        original_start = backend_main.start_ws_server_thread
        original_main = backend_main.main
        original_sleep = backend_main.time.sleep

        try:
            backend_main.start_ws_server_thread = lambda ready_event: object()
            backend_main.main = lambda: None
            backend_main.time.sleep = lambda _: None

            exit_code = backend_main.bootstrap_app(ws_ready_timeout=0.01)

            self.assertEqual(exit_code, 1)
        finally:
            backend_main.start_ws_server_thread = original_start
            backend_main.main = original_main
            backend_main.time.sleep = original_sleep

    def test_bootstrap_runs_runtime_when_ws_becomes_ready(self):
        original_start = backend_main.start_ws_server_thread
        original_main = backend_main.main
        original_sleep = backend_main.time.sleep
        calls: list[str] = []

        try:
            def fake_start(ready_event):
                ready_event.set()
                return object()

            def fake_main():
                calls.append("main")

            backend_main.start_ws_server_thread = fake_start
            backend_main.main = fake_main
            backend_main.time.sleep = lambda _: None

            exit_code = backend_main.bootstrap_app(ws_ready_timeout=0.01)

            self.assertEqual(exit_code, 0)
            self.assertEqual(calls, ["main"])
        finally:
            backend_main.start_ws_server_thread = original_start
            backend_main.main = original_main
            backend_main.time.sleep = original_sleep


if __name__ == "__main__":
    unittest.main()
