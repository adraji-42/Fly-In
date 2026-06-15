from map import Map
from typing import Dict, List
from drone import DroneScheduler


class Simulation:
    def __init__(self, _map: Map) -> None:
        self.__map = _map

    def run(self) -> None:
        turns_moves: Dict[int, List[str]] = {}
        for drone in self.__map.drones:
            DroneScheduler.schedule(drone)
            for event in drone.events:
                if event.time not in turns_moves:
                    turns_moves[event.time] = []
                turns_moves[event.time].append(f"{drone}-{event.token}")

        for turn in sorted(turns_moves.keys()):
            print(f"Turn {turn}: {' '.join(turns_moves[turn])}")
