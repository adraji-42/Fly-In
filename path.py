from .hub import EndHub, Hub
from itertools import count
from .mytypes import HubType
from .connection import Connection
from heapq import heappop, heappush
from typing import Set, List, Dict, Tuple, Optional, cast


class Path:
    def __init__(
        self,
        hubs: List[Hub],
        base_cost: int
    ) -> None:
        self.__hubs = hubs
        self.__base_cost = base_cost

    @property
    def hubs(self) -> List[Hub]:
        return self.__hubs

    @property
    def base_cost(self) -> int:
        return self.__base_cost


class PathFinder:
    @staticmethod
    def __next_cost(
        current_cost: int,
        current: Hub,
        connection: Connection
    ) -> int:
        move_cost = cast(int, connection.hub_to.cost)
        wait_cost = max(
            connection.nearest_reservation(current_cost),
            connection.hub_to.nearest_reservation(current_cost + move_cost) - move_cost
        ) - current_cost
        return current_cost + move_cost + wait_cost

    @classmethod
    def find_path(cls, start_hub: Hub, time: int = 0) -> Optional[Path]:
        unique = count()
        buckets: Dict[
            int,
            List[Tuple[int, int, Hub, List[Hub], List[Connection]]],
        ] = {}

        buckets[time] = []
        heappush(
            buckets[time],
            (1, next(unique), start_hub, [start_hub], [])
        )
        current_cost = time

        while buckets:
            if current_cost not in buckets:
                current_cost = min(buckets)
                continue

            priority, _, current, hubs, connections = heappop(
                buckets[current_cost]
            )

            if not buckets[current_cost]:
                del buckets[current_cost]

            if isinstance(current, EndHub):
                return Path(hubs, current_cost)

            visited: Set[str] = {hub.name for hub in hubs}

            for connection in current.connections.values():
                neighbour = connection.hub_to
                if neighbour.type is HubType.BLOCKED:
                    continue
                if neighbour.name in visited:
                    continue

                next_cost: int = cls.__next_cost(
                    current_cost, current, connection
                )

                if current == start_hub:
                    next_priority = (
                        0 if neighbour.type is HubType.PRIORITY else 1
                    )
                else:
                    next_priority = priority

                if next_cost not in buckets:
                    buckets[next_cost] = []
                heappush(
                    buckets[next_cost],
                    (
                        next_priority,
                        next(unique),
                        neighbour,
                        hubs + [neighbour],
                        connections + [connection],
                    ),
                )

        return None
