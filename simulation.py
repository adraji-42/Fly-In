from map import Map
from drone import DroneScheduler
from typing import Dict, List, Generator


class Simulation:
    """
    Manages the execution of the drone routing simulation.

    Coordinates drones scheduling on the map and collects simulation events
    to generate chronological output turns.
    """
    def __init__(self, _map: Map) -> None:
        """
        Initializes the Simulation instance.

        Args:
            _map (Map): The map instance containing hubs, connections, and drones.
        """
        self.__map = _map

    def run(self) -> Generator[str, None, None]:
        """
        Runs the simulation and yields the output line for each turn.

        Yields:
            str: A formatted string representing the moves of all drones during a single turn.
        """
        turns_moves: Dict[int, List[str]] = {}
        for drone in self.__map.drones:
            DroneScheduler.schedule(drone)
            for event in drone.events:
                if event.time not in turns_moves:
                    turns_moves[event.time] = []
                turns_moves[event.time].append(f"{drone}-{event.token}")

        for turn in sorted(turns_moves.keys()):
            yield ' '.join(turns_moves[turn])
