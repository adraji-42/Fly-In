from typing import Optional

from hub import Hub


class Drone:
    def __init__(self, drone_id: int, start_hub: Hub) -> None:
        self.__drone_id = drone_id
        self.__current_hub: Optional[Hub] = start_hub
        self.__previous_hub: Optional[Hub] = None
        self.__flight_origin: Optional[Hub] = None
        self.__flight_target: Optional[Hub] = None

    @property
    def drone_id(self) -> int:
        return self.__drone_id

    @property
    def current_hub(self) -> Optional[Hub]:
        return self.__current_hub

    @property
    def previous_hub(self) -> Optional[Hub]:
        return self.__previous_hub

    @property
    def flight_target(self) -> Optional[Hub]:
        return self.__flight_target

    @property
    def is_in_flight(self) -> bool:
        return self.__flight_target is not None

    def move_to(self, hub: Hub) -> None:
        self.__previous_hub = self.__current_hub
        self.__current_hub = hub

    def enter_restricted_transit(self, target: Hub) -> None:
        self.__flight_origin = self.__current_hub
        self.__current_hub = None
        self.__flight_target = target

    def land(self) -> Hub:
        if self.__flight_target is None:
            raise RuntimeError("Drone is not in flight")

        target = self.__flight_target
        self.__previous_hub = self.__flight_origin
        self.__current_hub = target
        self.__flight_origin = None
        self.__flight_target = None
        return target

    def is_at(self, hub: Hub) -> bool:
        return self.__current_hub is hub
