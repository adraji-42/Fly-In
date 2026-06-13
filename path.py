from __future__ import annotations

from hub import EndHub, Hub
from itertools import count
from mytyping import ZoneType
from connection import Connection
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Set, List, Dict, Tuple


@dataclass(frozen=True)
class PathStep:
    source: Hub
    connection: Connection
    destination: Hub

    @property
    def travel_time(self) -> int:
        if self.destination.type is ZoneType.RESTRICTED:
            return 2
        return 1

    @property
    def connection_name(self) -> str:
        return f"{self.source.name}-{self.destination.name}"

    @property
    def edge_key(self) -> Tuple[str, str]:
        names = sorted((self.source.name, self.destination.name))
        return names[0], names[1]


class Path:
    def __init__(
        self,
        hubs: List[Hub],
        connections: List[Connection],
        base_cost: int,
    ) -> None:
        if len(hubs) < 2:
            raise ValueError(
                "A Path must contain at least a start and an end hub."
            )
        self.__hubs = hubs
        self.__base_cost = base_cost
        self.__steps = [
            PathStep(hubs[index], connection, hubs[index + 1])
            for index, connection in enumerate(connections)
        ]

    @property
    def hubs(self) -> List[Hub]:
        return self.__hubs

    @property
    def steps(self) -> List[PathStep]:
        return self.__steps

    @property
    def base_cost(self) -> int:
        return self.__base_cost

    @property
    def first_hub(self) -> Hub:
        return self.__hubs[1]

    @property
    def priority_score(self) -> int:
        return sum(hub.type is not ZoneType.PRIORITY for hub in self.__hubs)

    def __repr__(self) -> str:
        names = " -> ".join(hub.name for hub in self.__hubs)
        return f"Path(base_cost={self.__base_cost}, hubs=[{names}])"


class PathFinder:

    @staticmethod
    def __hub_cost(zone_type: ZoneType) -> int:
        if zone_type is ZoneType.RESTRICTED:
            return 2
        return 1

    @classmethod
    def find_paths(cls, start_hub: Hub, nb_drones: int) -> List[Path]:
        paths: List[Path] = []
        unique = count()
        buckets: Dict[
            int,
            List[Tuple[int, int, Hub, List[Hub], List[Connection]]],
        ] = {}

        buckets[0] = []
        heappush(
            buckets[0],
            (1, next(unique), start_hub, [start_hub], [])
        )
        current_cost = 0

        while buckets and len(paths) < nb_drones:
            if current_cost not in buckets:
                current_cost = min(buckets)
                continue

            priority, _, current, hubs, connections = heappop(
                buckets[current_cost]
            )

            if not buckets[current_cost]:
                del buckets[current_cost]

            if isinstance(current, EndHub):
                paths.append(Path(hubs, connections, current_cost))
                continue

            visited: Set[str] = {hub.name for hub in hubs}

            for connection in current.connections:
                neighbour = connection.hub_to
                if neighbour.type is ZoneType.BLOCKED:
                    continue
                if neighbour.name in visited:
                    continue

                next_cost: int = current_cost + cls.__hub_cost(
                    neighbour.type
                )

                if current == start_hub:
                    next_priority = (
                        0 if neighbour.type is ZoneType.PRIORITY else 1
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

        return paths
