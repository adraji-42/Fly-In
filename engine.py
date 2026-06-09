from map import Map
from drone import Drone
from exceptions import MapError
from typing import Generator, List


class SimulationEngine:

    def __init__(self, fly_map: Map) -> None:
        self.__map = fly_map
        self.__drones = [
            Drone(index, fly_map.start_hub, fly_map.end_hub)
            for index in range(1, fly_map.nb_drones + 1)
        ]

    @property
    def all_finished(self) -> bool:
        return all(
            drone.current_hub == self.__map.end_hub
            for drone in self.__drones
        )

    def soulation_generator(self) -> Generator[str, None, None]:
        while not self.all_finished:
            moves: List[str] = []
            active_drones = [
                d for d in self.__drones
                if d.current_hub != self.__map.end_hub or d.in_transit
            ]
            stuck_count = 0

            for drone in active_drones:
                if drone.in_transit:
                    assert drone._Drone__transit_destination is not None
                    move = drone.move_to(drone._Drone__transit_destination)
                    moves.append(move)
                    continue

                next_hub_name = drone.next_hub

                if next_hub_name == "":
                    continue

                if next_hub_name is None:
                    stuck_count += 1
                    continue

                hub = self.__map.hubs.get(next_hub_name, self.__map.end_hub)
                move = drone.move_to(hub)
                moves.append(move)

            if stuck_count == len(active_drones):
                raise MapError(
                    "The map is not solvable: all drones are stuck."
                )

            if moves:
                yield ' '.join(moves)
