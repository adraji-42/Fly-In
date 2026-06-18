from __future__ import annotations

from hub import Hub
from exceptions import MapLogicError, ErrorInfo
from path import Path, PathFinder
from dataclasses import dataclass
from typing import List, cast, Optional


@dataclass(slots=True, frozen=True)
class DroneEvent:
    time: int
    token: str


class DroneScheduler:

    @staticmethod
    def schedule(
        drone: Drone, time: int = 0,
    ) -> None:
        path: Optional[Path] = PathFinder.find_path(
            drone.current_hub, time,
        )
        if not path:
            raise MapLogicError(ErrorInfo(
                line_number=0,
                line_content="",
                error_start=0,
                error_end=0,
                reason=(
                    "no path found in the map"
                ),
                expected=(
                    "a reachable path from"
                    " start to end hub"
                ),
                how_to_fix=(
                    "verify the map has a connected"
                    " path that is not fully blocked"
                ),
            ))
        for i in range(1, len(path.hubs)):
            current = path.hubs[i - 1]
            next_hub = path.hubs[i]
            connection = path.hubs[i - 1].connections[next_hub.name]

            cost = cast(int, next_hub.cost)
            while (
                not connection.can_reserve(time)
                or not next_hub.can_reserve(time + cost)
            ):
                current.reserve(time)
                time += 1

            connection.reserve(time)
            next_hub.reserve(time + cost)

            if cost == 2:
                drone.add_event(DroneEvent(time, str(connection)))
                drone.add_event(DroneEvent(time + 1, str(next_hub)))
            else:
                drone.add_event(DroneEvent(time, str(next_hub)))

            time += cost


class Drone:
    def __init__(self, drone_id: int, current_hub: Hub) -> None:
        self.__id = drone_id
        self.current_hub: Hub = current_hub
        self.__events: List[DroneEvent] = []

    @property
    def id(self) -> int:
        return self.__id

    @property
    def events(self) -> List[DroneEvent]:
        return self.__events

    def add_event(self, event: DroneEvent) -> None:
        self.__events.append(event)

    def __str__(self) -> str:
        return f"D{self.__id}"
