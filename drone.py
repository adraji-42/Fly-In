from __future__ import annotations

from typing import List
from hub import Hub, HubType
from exceptions import MapError
from path import Path, PathFinder
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DroneEvent:
    time: int
    token: str


class DroneScheduler:

    @staticmethod
    def schedule(drone: Drone, time: int = 0) -> None:
        path: Path = PathFinder.find_path(drone.current_hub, time)
        if not path:
            raise MapError(
                "No path found in the map"
            )
        for i in range(1, len(path.hubs)):
            hub = path.hubs[i]
            connection = hub.connections[path.hubs[i - 1].name]

            cost = hub.cost
            time = max(
                connection.nearest_reservation(time),
                hub.nearest_reservation(time + cost) - cost
            )
            hub.reserve(time + cost)
            connection.reserve(time)
            
            if cost == 2:
                drone.add_event(DroneEvent(time, str(connection)))
                drone.add_event(DroneEvent(time + 1, str(hub)))
            else:
                drone.add_event(DroneEvent(time, str(hub)))
                
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
