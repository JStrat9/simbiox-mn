from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np


class FramePresenter(Protocol):
    def present(self, frame: np.ndarray):
        ...

    def close(self):
        ...


class RuntimeControl(Protocol):
    def should_stop(self) -> bool:
        ...


class NullFramePresenter:
    def present(self, frame: np.ndarray):
        return None

    def close(self):
        return None


class OpenCVFramePresenter:
    def __init__(self, window_name: str = "Side Camera"):
        self.window_name = window_name

    def present(self, frame: np.ndarray):
        cv2.imshow(self.window_name, frame)

    def close(self):
        cv2.destroyAllWindows()


class HeadlessRuntimeControl:
    def should_stop(self) -> bool:
        return False


class OpenCVKeypressControl:
    def __init__(self, quit_key: str = "q", wait_ms: int = 1):
        if len(quit_key) != 1:
            raise ValueError("quit_key must be a single character")
        self.quit_code = ord(quit_key)
        self.wait_ms = wait_ms

    def should_stop(self) -> bool:
        return (cv2.waitKey(self.wait_ms) & 0xFF) == self.quit_code
