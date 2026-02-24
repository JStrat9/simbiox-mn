from __future__ import annotations

from typing import Protocol


class SessionUpdatePublisher(Protocol):
    def publish(self) -> None:
        ...


class NullSessionUpdatePublisher:
    def publish(self) -> None:
        return
