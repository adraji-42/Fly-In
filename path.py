from itertools import count
from mytypes import HubType
from connection import Connection
from heapq import heappop, heappush
from hub import Hub, EndHub
from typing import Set, List, Dict, Tuple, Optional, cast


class Path:
    """
    Represents a computed path of hubs from start to end.

    Attributes:
        hubs (List[Hub]): The sequence of hubs comprising the path.
        base_cost (int): The starting cost/time when the path routing began.
    """

    def __init__(self, hubs: List[Hub], base_cost: int) -> None:
        """
        Initializes a Path.

        Args:
            hubs (List[Hub]): The list of hubs in the path.
            base_cost (int): The base cost for the path.
        """
        self.__hubs = hubs
        self.__base_cost = base_cost

    @property
    def hubs(self) -> List[Hub]:
        """List[Hub]: The list of hubs in this path."""
        return self.__hubs

    @property
    def base_cost(self) -> int:
        """int: The initial cost of starting this path."""
        return self.__base_cost


class PathFinder:
    """
    Utility class for finding paths between hubs using Dijkstra's algorithm
    variant.
    """

    @staticmethod
    def __wait_time(current_cost: int, connection: Connection) -> int:
        """
        Calculates the waiting time required before a connection and its
        destination hub become available.

        Args:
            current_cost (int): The current accumulated cost/time.
            connection (Connection): The connection being evaluated.

        Returns:
            int: The number of turns to wait.
        """
        wait_cost = 0
        cost = cast(int, connection.hub_to.cost)
        while not all(
            connection.can_reserve(current_cost + wait_cost + t)
            for t in range(cost)
        ) or not connection.hub_to.can_reserve(
            current_cost + cost + wait_cost
        ):
            wait_cost += 1
        return wait_cost

    @classmethod
    def find_path(cls, start_hub: Hub, time: int = 0) -> Optional[Path]:
        """
        Finds the optimal path from the start_hub to an EndHub.

        Args:
            start_hub (Hub): The hub from which to start the search.
            time (int): The starting time. Defaults to 0.

        Returns:
            Optional[Path]: The found Path, or None if no path exists.
        """
        unique = count()
        buckets: Dict[
            int,
            List[Tuple[int, int, int, Hub, List[Hub], List[Connection]]],
        ] = {}

        buckets[time] = []
        heappush(
            buckets[time], (1, 0, next(unique), start_hub, [start_hub], [])
        )
        current_cost = time

        while buckets:
            if current_cost not in buckets:
                current_cost = min(buckets)
                continue

            priority, wait, _, current, hubs, connections = heappop(
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

                next_wait: int = cls.__wait_time(current_cost, connection)
                next_cost: int = (
                    current_cost + next_wait + cast(int, neighbour.cost)
                )

                next_priority: int = priority
                if current == start_hub:
                    next_priority = (
                        0 if neighbour.type
                        is HubType.PRIORITY else 1
                    )
                else:
                    next_wait = wait

                if next_cost not in buckets:
                    buckets[next_cost] = []
                heappush(
                    buckets[next_cost],
                    (
                        next_priority,
                        next_wait,
                        next(unique),
                        neighbour,
                        hubs + [neighbour],
                        connections + [connection],
                    ),
                )

        return None
