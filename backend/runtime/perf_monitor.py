from __future__ import annotations

import os
import time
from typing import Protocol

import psutil


class PerfReporter(Protocol):
    def tick(self):
        ...


class NullPerfReporter:
    def tick(self):
        return None


class PsutilPerfReporter:
    def __init__(self, *, label: str = "MAIN", interval_s: float = 1.0):
        self.label = label
        self.interval_s = interval_s
        self.process = psutil.Process(os.getpid())
        self.last_print = time.time()
        self.frames = 0

    def tick(self):
        self.frames += 1
        now = time.time()
        if now - self.last_print < self.interval_s:
            return

        fps = self.frames / (now - self.last_print)
        cpu = psutil.cpu_percent()
        ram = self.process.memory_info().rss / 1024 / 1024
        print(f"[PERF][{self.label}] fps={fps:.0f} cpu={cpu}% ram={ram:.0f}MB")

        self.last_print = now
        self.frames = 0
