from map import Map
from drone import Drone
from mytyping import ZoneType
from exceptions import MapError
from path import PathFinder, Path
from typing import Generator, List


class SimulationEngine:

    def __init__(self, fly_map: Map) -> None:
        self.__map: Map = fly_map
        self.__drones: List[Drone] = [
            Drone(index, fly_map.start_hub)
            for index in range(1, fly_map.nb_drones + 1)
        ]
        self.__paths: List[Path] = sorted(
            PathFinder.find_paths(fly_map.start_hub),
            key=lambda p: (p.cost, p.first_hub.type is not ZoneType.PRIORITY)
        )

    @property
    def all_finished(self) -> bool:
        return all(
            drone.current_hub == self.__map.end_hub
            for drone in self.__drones
        )

    def __set_path_factors(self) -> None:
        self.__paths[0].factors = 0
        for path in self.__paths[1:]:
            path.factors = path.cost - self.__paths[0].cost

    def __set_drones_paths(self) -> None:
        paths = [
            p for p in self.__paths[1:] if p.factors < self.__map.nb_drones
        ]

        for path in paths:
            for drone in self.__drones:
                if drone.path is None:
                    continue
                if drone._id % path.factors > 1:
                    break
                drone.path = path

    def soulation_generator(self) -> Generator[str, None, None]:
        self.__set_path_factors()
        self.__set_drones_paths()

        while not self.all_finished:
            for drone in self.__drones:
                if drone.current_hub == self.__map.end_hub:
                    continue
