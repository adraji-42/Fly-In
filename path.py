from __future__ import annotations

from hub import Hub, EndHub
from mytyping import ZoneType
from typing import List, Tuple, Optional


HUB_COST = lambda zone_type: 2 if zone_type is ZoneType.RESTRICTED else 1


class PathFinder:

    @staticmethod
    def find_paths(current_hub: Hub) -> List[Path]:
        paths: List[Path] = []
        stack: List[Tuple[Hub, List[Hub]]] = [
            (current_hub, [current_hub])
        ]

        while stack:
            current, path = stack.pop()

            if isinstance(current, EndHub):
                paths.append(Path(path))
                continue

            visited_names = {h.name for h in path}

            for connection in current.connections:
                neighbour = connection.hub_to
                if (
                    neighbour.name in visited_names
                    or not connection.can_crossing
                    or not neighbour.can_land
                    or neighbour.type is not ZoneType.BLOCKED
                ):
                    continue
                stack.append((neighbour, path + [neighbour]))

        return paths


class Path:
    def __init__(self, path: List[Hub]) -> None:
        self.__path = path
        self.__cost = sum(HUB_COST(hub.type) for hub in path[1:])
        self.__nb_drones_passing = 0

    @property
    def first_hub(self) -> Hub:
        return self.__path[1]

    @property
    def cost(self) -> int:
        return self.__cost

    def drone_pass(self) -> None:
        self.__nb_drones_passing += 1
