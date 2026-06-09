from hub import Hub
from mytyping import ZoneType
from typing import Optional, Tuple, List


# Turn cost to enter a hub based on zone type.
# BLOCKED is never entered. PRIORITY costs 1 but is preferred.
HUB_COST: dict[ZoneType, int] = {
    ZoneType.NORMAL:     1,
    ZoneType.PRIORITY:   1,
    ZoneType.RESTRICTED: 2,
}


class Drone:

    def __init__(self, id: int, hub: Hub, end_hub: Hub) -> None:
        self._id = id
        self.__current_hub: Hub = hub
        self.__end_hub: Hub = end_hub
        self.__transit_destination: Optional[Hub] = None

    @property
    def current_hub(self) -> Hub:
        return self.__current_hub

    @property
    def in_transit(self) -> bool:
        return self.__transit_destination is not None

    def __all_paths(self) -> List[List[Hub]]:

        paths: List[List[Hub]] = []
        stack: List[Tuple[Hub, List[Hub]]] = [
            (self.__current_hub, [self.__current_hub])
        ]

        while stack:
            current, path = stack.pop()

            if current is self.__end_hub:
                paths.append(path)
                continue

            visited_names = {h.name for h in path}

            for connection in current.connections:
                neighbour = connection.hub_to
                if (
                    neighbour.name in visited_names
                    or not connection.can_crossing
                    or not neighbour.can_land
                    or neighbour.type == ZoneType.BLOCKED
                ):
                    continue
                stack.append((neighbour, path + [neighbour]))

        return paths

    def __path_cost(self, path: List[Hub]) -> int:
        return sum(HUB_COST[hub.type] for hub in path[1:])

    @property
    def next_hub(self) -> Optional[str]:

        if self.__current_hub is self.__end_hub:
            return ""

        all_paths = self.__all_paths()

        if not all_paths:
            return None

        return min(all_paths, key=self.__path_cost)

    def move_to(self, hub: Hub) -> str:

        if self.__transit_destination is hub:
            hub.land()
            self.__current_hub = hub
            self.__transit_destination = None
            return f"D{self._id}-{hub.name}"

        if hub.type is ZoneType.RESTRICTED:
            self.__current_hub.leaving()
            self.__transit_destination = hub
            connection_name = f"{self.__current_hub.name}-{hub.name}"
            return f"D{self._id}-{connection_name}"

        self.__current_hub.leaving()
        hub.land()
        self.__current_hub = hub
        return f"D{self._id}-{hub.name}"
