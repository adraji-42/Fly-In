from __future__ import annotations

from map import Map
from drone import Drone
from path import Path, PathFinder
from mytyping import ZoneType
from typing import Generator, List, Optional


class DroneScheduler:

    def __init__(self, paths: List[Path]) -> None:
        if not paths:
            raise ValueError("No viable paths found in the map.")
        self.__paths: List[Path] = sorted(
            paths,
            key=lambda p: (
                p.base_cost,
                p.first_hub.type is not ZoneType.PRIORITY,
            ),
        )

    def assign(self, drone: Drone) -> Path:
        best: Path = self.__paths[0]
        for path in self.__paths[1:]:
            if path.predict_arrival_turn(0) < best.predict_arrival_turn(0):
                best = path
        best.calculate_arrival_turn(0)
        drone.path = best
        return best

    def release(self, drone: Drone) -> None:
        if drone.path is not None:
            drone.path.release_drone()


class SimulationEngine:

    def __init__(self, fly_map: Map) -> None:
        self.__map: Map = fly_map
        self.__drones: List[Drone] = [
            Drone(index, fly_map.start_hub)
            for index in range(1, fly_map.nb_drones + 1)
        ]

        raw_paths = PathFinder.find_paths(fly_map.start_hub, fly_map.nb_drones)
        self.__scheduler: DroneScheduler = DroneScheduler(raw_paths)

        for drone in self.__drones:
            self.__scheduler.assign(drone)

    @property
    def all_finished(self) -> bool:
        return all(drone.finished for drone in self.__drones)

    def solution_generator(self) -> Generator[str, None, None]:

        while not self.all_finished:
            turn_tokens: List[str] = []

            for drone in self.__drones:
                if drone.finished:
                    continue

                token: Optional[str] = drone.step()
                if token is not None:
                    turn_tokens.append(token)

                    if drone.finished:
                        self.__scheduler.release(drone)

            if turn_tokens:
                yield " ".join(turn_tokens)
