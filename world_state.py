from typing import Dict, Iterable, Optional

from connection import Connection
from drone import Drone
from hub import Hub


class WorldState:
    def __init__(
        self,
        hubs: Dict[str, Hub],
        drones: Iterable[Drone],
    ) -> None:
        self.__hubs = hubs
        self.__hub_capacity = {
            name: hub.max_drones for name, hub in hubs.items()
        }
        self.__hub_available = dict(self.__hub_capacity)
        self.__link_available = self.__build_link_capacities(hubs)

        for drone in drones:
            if drone.current_hub is not None:
                self.__hub_available[drone.current_hub.name] -= 1
            if drone.flight_target is not None:
                self.__hub_available[drone.flight_target.name] -= 1

    def can_use_connection(
        self,
        from_hub: Hub,
        connection: Connection,
    ) -> bool:
        key = self.__link_key(from_hub.name, connection.zone_to)
        return self.__link_available.get(key, 0) > 0

    def can_enter_hub(self, hub: Hub) -> bool:
        return self.__hub_available.get(hub.name, 0) > 0

    def connection_between(
        self,
        from_hub: Hub,
        to_hub: Hub,
    ) -> Optional[Connection]:
        for connection in from_hub.connections:
            if connection.zone_to == to_hub.name:
                return connection
        return None

    def release_hub(self, hub: Hub) -> None:
        self.__hub_available[hub.name] += 1

    def occupy_hub(self, hub: Hub) -> None:
        self.__hub_available[hub.name] -= 1

    def use_connection(self, from_hub: Hub, to_hub: Hub) -> None:
        key = self.__link_key(from_hub.name, to_hub.name)
        self.__link_available[key] -= 1

    def bottleneck_pressure(self, hub: Hub) -> float:
        capacity = self.__hub_capacity[hub.name]
        available = self.__hub_available[hub.name]
        occupied = capacity - available
        return occupied / capacity

    @classmethod
    def __build_link_capacities(
        cls,
        hubs: Dict[str, Hub],
    ) -> Dict[frozenset[str], int]:
        capacities: Dict[frozenset[str], int] = {}
        for hub in hubs.values():
            for connection in hub.connections:
                if connection.zone_to not in hubs:
                    continue
                key = cls.__link_key(hub.name, connection.zone_to)
                capacities[key] = connection.max_link_capacity
        return capacities

    @staticmethod
    def __link_key(first_hub: str, second_hub: str) -> frozenset[str]:
        return frozenset({first_hub, second_hub})
