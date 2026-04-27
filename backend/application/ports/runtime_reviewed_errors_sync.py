from __future__ import annotations

from typing import Protocol


class RuntimeReviewedErrorsSyncPort(Protocol):
    def clear(self, session_person_id: str) -> None:
        ...
