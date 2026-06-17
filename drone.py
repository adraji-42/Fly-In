from __future__ import annotations

from hub import Hub
from exceptions import MapError
from path import Path, PathFinder
from dataclasses import dataclass
from typing import List, cast, Optional


@dataclass(slots=True, frozen=True)
class DroneEvent:
    time: int
    token: str


class DroneScheduler:

    @staticmethod
    def schedule(drone: Drone, time: int = 0) -> None:
        path: Optional[Path] = PathFinder.find_path(drone.current_hub, time)
        if not path:
            raise MapError(
                "No path found in the map"
            )
        for i in range(1, len(path.hubs)):
            current = path.hubs[i - 1]
            next_hub = path.hubs[i]
            connection = path.hubs[i - 1].connections[next_hub.name]

            cost = cast(int, next_hub.cost)
            while (
                not connection.can_reserve(time)
                or not connection.hub_to.can_reserve(time + cost)
            ):
                current.reserve(time)
                time += 1

            if cost == 2:
                connection.reserve(time)
                next_hub.reserve(time + cost)
                drone.add_event(DroneEvent(time, str(connection)))
                drone.add_event(DroneEvent(time + 1, str(next_hub)))
            else:
                next_hub.reserve(time + cost)
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
