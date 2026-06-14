from __future__ import annotations

from hub import Hub
from path import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MovementEvent:
    turn: int
    token: str


class Drone:
    def __init__(self, drone_id: int, hub: Hub) -> None:
        self.__id = drone_id
        self.__start_hub = hub
        self.__path: Optional[Path] = None
        self.__events: List[MovementEvent] = []
        self.__finished_turn: Optional[int] = None

    @property
    def id(self) -> int:
        return self.__id

    @property
    def start_hub(self) -> Hub:
        return self.__start_hub

    @property
    def path(self) -> Optional[Path]:
        return self.__path

    @property
    def events(self) -> List[MovementEvent]:
        return self.__events

    @property
    def finished(self) -> bool:
        return self.__finished_turn is not None

    def assign_plan(
        self,
        path: Path,
        events: List[MovementEvent],
        finished_turn: int,
    ) -> None:
        self.__path = path
        self.__events = events
        self.__finished_turn = finished_turn

    def __repr__(self) -> str:
        return f"Drone(id={self.__id}, finished={self.finished})"
