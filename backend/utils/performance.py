# performance.py
import time
import psutil
from collections import defaultdict

class PerformanceLogger:
    """
    Logger central para medir FPS, latencia, CPU y RAM
    de distintos módulos o cámaras en el backend.
    """
    def __init__(self):
        self.counters = defaultdict(lambda: {"frames": 0, "last_time": time.time()})
        self.process = psutil.Process()
    
    def log_frame(self, name: str, latency_ms: float = 0.0):
        """
        Llamar cada vez que se procesa un frame.
        name: identificador del módulo/cámara
        latency_ms: tiempo que tarda en procesarse el frame
        """
        counter = self.counters[name]
        counter["frames"] += 1
        now = time.time()
        elapsed = now - counter["last_time"]

        if elapsed >= 1.0:  # cada segundo
            fps = counter["frames"] / elapsed
            counter["frames"] = 0
            counter["last_time"] = now

            cpu = psutil.cpu_percent(interval=None)
            ram = self.process.memory_info().rss / (1024 * 1024)  # MB

            print(f"[PERF][{name.upper()}] fps={fps:.0f} latency={latency_ms:.0f}ms cpu={cpu:.0f}% ram={ram:.0f}MB")