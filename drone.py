from __future__ import annotations

from hub import Hub
from exceptions import MapLogicError, ErrorInfo
from path import Path, PathFinder
from dataclasses import dataclass
from typing import List, cast, Optional


@dataclass(slots=True, frozen=True)
class DroneEvent:
    """
    Represents an event corresponding to a drone arriving at a specific token
    (hub or connection) at a certain time.

    Attributes:
        time (int): The turn number when this event occurs.
        token (str): The string representation of the hub or connection the
            drone reaches.
    """

    time: int
    token: str


class DroneScheduler:
    """
    Handles scheduling of a drone's path.
    """

    @staticmethod
    def schedule(drone: Drone, time: int = 0) -> None:
        """
        Schedules a single drone from its current hub to the end hub.

        Finds a path and reserves the appropriate hubs and connections,
        generating
        events for the drone's movements.

        Args:
            drone (Drone): The drone to be scheduled.
            time (int): The starting time for the drone's schedule. Defaults
                to 0.

        Raises:
            MapLogicError: If no valid path can be found for the drone.
        """
        path: Optional[Path] = PathFinder.find_path(
            drone.current_hub,
            time,
        )
        if not path:
            raise MapLogicError(
                ErrorInfo(
                    line_number=0,
                    line_content="",
                    error_start=0,
                    error_end=0,
                    reason=("no path found in the map"),
                    expected=("a reachable path from" " start to end hub"),
                    how_to_fix=(
                        "verify the map has a connected"
                        " path that is not fully blocked"
                    ),
                )
            )
        for i in range(1, len(path.hubs)):
            current = path.hubs[i - 1]
            next_hub = path.hubs[i]
            connection = path.hubs[i - 1].connections[next_hub.name]

            cost = cast(int, next_hub.cost)
            while not all(
                connection.can_reserve(time + t) for t in range(cost)
            ) or not next_hub.can_reserve(time + cost):
                current.reserve((time := time + 1))

            for t in range(cost):
                connection.reserve(time + t)
            next_hub.reserve(time + cost)

            if cost == 2:
                drone.add_event(DroneEvent(time, str(connection)))
                drone.add_event(DroneEvent(time + 1, str(next_hub)))
            else:
                drone.add_event(DroneEvent(time, str(next_hub)))

            time += cost


class Drone:
    """
    Represents a drone navigating the map.

    Tracks its ID, current hub location, and scheduled events over time.
    """

    def __init__(self, drone_id: int, current_hub: Hub) -> None:
        """
        Initializes a Drone instance.

        Args:
            drone_id (int): The unique identifier of the drone.
            current_hub (Hub): The hub where the drone initially spawns.
        """
        self.__id = drone_id
        self.current_hub: Hub = current_hub
        self.__events: List[DroneEvent] = []

    @property
    def id(self) -> int:
        """int: The unique identifier of the drone."""
        return self.__id

    @property
    def events(self) -> List[DroneEvent]:
        """List[DroneEvent]: The list of events generated for this drone's
        path."""
        return self.__events

    def add_event(self, event: DroneEvent) -> None:
        """
        Adds a new scheduling event to the drone's event list.

        Args:
            event (DroneEvent): The event to add.
        """
        self.__events.append(event)

    def __str__(self) -> str:
        """
        Returns the string representation of the drone.

        Returns:
            str: The string representation, e.g. "D1".
        """
        return f"D{self.__id}"
