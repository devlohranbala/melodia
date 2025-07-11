from typing import Protocol


class Controller(Protocol):
    """Protocol for controllers"""
    def initialize(self) -> None: ...
    def cleanup(self) -> None: ...