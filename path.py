from __future__ import annotations

from hub import Hub, EndHub
from mytyping import ZoneType
from typing import List, Optional, Tuple


_COST_THRESHOLD_FACTOR: int = 2


class PathFinder:

    @staticmethod
    def __hub_cost(zone_type: ZoneType) -> int:
        if zone_type is ZoneType.RESTRICTED:
            return 2
        return 1

    @classmethod
    def find_paths(cls, start_hub: Hub) -> List[Path]:

        paths: List[Path] = []
        shortest_cost: Optional[int] = None

        queue: List[Tuple[Hub, List[Hub], int]] = []
        queue.append((start_hub, [start_hub], 0))

        while queue:
            current, path, cost = queue.pop(0)

            if shortest_cost is not None:
                if cost > shortest_cost * _COST_THRESHOLD_FACTOR:
                    continue

            if isinstance(current, EndHub):
                paths.append(Path(path, cost))
                if shortest_cost is None or cost < shortest_cost:
                    shortest_cost = cost
                continue

            visited_names = {h.name for h in path}

            for connection in current.connections:
                neighbour = connection.hub_to

                if (
                    not neighbour.can_land
                    or not connection.can_crossing
                    or neighbour.name in visited_names
                ):
                    continue

                next_cost = cost + cls.__hub_cost(neighbour.type)

                if shortest_cost is not None:
                    if next_cost > shortest_cost * _COST_THRESHOLD_FACTOR:
                        continue

                queue.append((neighbour, path + [neighbour], next_cost))

        return paths


class Path:

    def __init__(self, hubs: List[Hub], base_cost: int) -> None:
        if len(hubs) < 2:
            raise ValueError(
                "A Path must contain at least a start and an end hub."
            )
        self.__hubs: List[Hub] = hubs
        self.__base_cost: int = base_cost
        self.__drone_count: int = 0

    @property
    def hubs(self) -> List[Hub]:
        return self.__hubs

    @property
    def base_cost(self) -> int:
        return self.__base_cost

    @property
    def drone_count(self) -> int:
        return self.__drone_count

    @property
    def actual_cost(self) -> int:
        return self.__base_cost + self.__drone_count

    @property
    def first_hub(self) -> Hub:
        return self.__hubs[1]

    def assign_drone(self) -> None:
        self.__drone_count += 1

    def release_drone(self) -> None:
        if self.__drone_count > 0:
            self.__drone_count -= 1

    def __repr__(self) -> str:
        names = " -> ".join(h.name for h in self.__hubs)
        return (
            f"Path(base_cost={self.__base_cost}, "
            f"drone_count={self.__drone_count}, hubs=[{names}])"
        )
