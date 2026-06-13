from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import List, Tuple

from connection import Connection
from hub import EndHub, Hub
from mytyping import ZoneType


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
        self.__connections = connections
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

    @staticmethod
    def __hub_priority(zone_type: ZoneType) -> int:
        if zone_type is ZoneType.PRIORITY:
            return 0
        if zone_type is ZoneType.NORMAL:
            return 1
        return 2

    @classmethod
    def find_paths(cls, start_hub: Hub, nb_drones: int) -> List[Path]:
        paths: List[Path] = []
        unique = count()
        queue: List[
            Tuple[int, int, int, int, Hub, List[Hub], List[Connection]]
        ] = []
        heappush(queue, (0, 0, 0, next(unique), start_hub, [start_hub], []))

        while queue and len(paths) < nb_drones:
            cost, priority, length, _, current, hubs, connections = heappop(
                queue
            )

            if isinstance(current, EndHub):
                paths.append(Path(hubs, connections, cost))
                continue

            visited = {hub.name for hub in hubs}
            next_connections = sorted(
                current.connections,
                key=lambda item: (
                    cls.__hub_cost(item.hub_to.type),
                    cls.__hub_priority(item.hub_to.type),
                    item.hub_to.name,
                ),
            )

            for connection in next_connections:
                neighbour = connection.hub_to
                if neighbour.type is ZoneType.BLOCKED:
                    continue
                if neighbour.name in visited:
                    continue
                next_cost = cost + cls.__hub_cost(neighbour.type)
                next_priority = priority + cls.__hub_priority(
                    neighbour.type
                )
                heappush(
                    queue,
                    (
                        next_cost,
                        next_priority,
                        length + 1,
                        next(unique),
                        neighbour,
                        hubs + [neighbour],
                        connections + [connection],
                    ),
                )

        return sorted(
            paths,
            key=lambda path: (
                path.base_cost,
                path.priority_score,
                len(path.hubs),
            ),
        )
