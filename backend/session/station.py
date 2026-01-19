# session/station.py

from dataclasses import dataclass

@dataclass
class Station:
    station_id: str
    exercise: str
    