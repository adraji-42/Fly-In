from collections import deque
from typing import Dict, Optional

from drone import Drone
from hub import EndHub, Hub
from mytyping import ZoneType
from world_state import WorldState


class Pathfinder:
    def __init__(self, hubs: Dict[str, Hub], end_hub: EndHub) -> None:
        self.__hubs = hubs
        self.__end_hub = end_hub

    def next_hub(
        self,
        drone: Drone,
        world_state: WorldState,
    ) -> Optional[Hub]:
        current_hub = drone.current_hub
        if current_hub is None or current_hub is self.__end_hub:
            return None

        return self.__search(drone, world_state)

    def __search(
        self,
        drone: Drone,
        world_state: WorldState,
    ) -> Optional[Hub]:
        current_hub = drone.current_hub
        if current_hub is None:
            return None

        queue = deque([current_hub])
        parents: Dict[str, Optional[str]] = {current_hub.name: None}

        while queue:
            hub = queue.popleft()
            if hub is self.__end_hub:
                break

            for next_hub in self.__neighbors(hub, drone, world_state):
                if next_hub.name in parents:
                    continue
                parents[next_hub.name] = hub.name
                queue.append(next_hub)

        if self.__end_hub.name not in parents:
            return None

        step_name = self.__end_hub.name
        while parents[step_name] != current_hub.name:
            parent = parents[step_name]
            if parent is None:
                return None
            step_name = parent
        return self.__hubs[step_name]

    def __neighbors(
        self,
        hub: Hub,
        drone: Drone,
        world_state: WorldState,
    ) -> list[Hub]:
        neighbors = []
        previous_hub = drone.previous_hub

        connections = sorted(
            hub.connections,
            key=lambda item: item.zone_to,
        )
        for connection in connections:
            if not world_state.can_use_connection(hub, connection):
                continue

            next_hub = self.__hubs[connection.zone_to]
            if next_hub.zone == ZoneType.BLOCKED:
                continue
            if (
                hub is drone.current_hub
                and next_hub is previous_hub
            ):
                continue
            if next_hub is not self.__end_hub:
                if not world_state.can_enter_hub(next_hub):
                    continue
            elif not world_state.can_enter_hub(next_hub):
                continue

            neighbors.append(next_hub)

        return neighbors
