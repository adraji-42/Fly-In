from typing import Dict, Iterable, List, Tuple

from drone import Drone
from hub import Hub
from map import Map
from mytyping import ZoneType
from pathfinder import Pathfinder
from world_state import WorldState


class SimulationEngine:
    def __init__(self, fly_map: Map) -> None:
        self.__map = fly_map
        self.__hubs = self.__build_hubs(fly_map)
        self.__drones = [
            Drone(index, fly_map.start_hub)
            for index in range(1, fly_map.nb_drones + 1)
        ]
        self.__pathfinder = Pathfinder(self.__hubs, fly_map.end_hub)

    def run(self) -> List[List[str]]:
        turns: List[List[str]] = []

        while not self.__finished:
            turn_moves, progressed = self.__run_turn()
            if not progressed:
                raise RuntimeError("Simulation cannot progress")
            turns.append(turn_moves)

        return turns

    @property
    def __finished(self) -> bool:
        return all(drone.is_at(self.__map.end_hub) for drone in self.__drones)

    def __run_turn(self) -> Tuple[List[str], bool]:
        world_state = WorldState(self.__hubs, self.__drones)
        turn_moves = []
        progressed = False

        for drone in self.__ordered_drones(world_state):
            if drone.is_in_flight:
                target = drone.land()
                turn_moves.append(self.__format_move(drone, target))
                progressed = True
                continue

            next_hub = self.__pathfinder.next_hub(drone, world_state)
            if next_hub is None or drone.current_hub is None:
                continue

            current_hub = drone.current_hub
            world_state.release_hub(current_hub)
            world_state.use_connection(current_hub, next_hub)

            if next_hub.zone == ZoneType.RESTRICTED:
                world_state.occupy_hub(next_hub)
                drone.enter_restricted_transit(next_hub)
                progressed = True
            else:
                world_state.occupy_hub(next_hub)
                drone.move_to(next_hub)
                turn_moves.append(self.__format_move(drone, next_hub))
                progressed = True

        return turn_moves, progressed

    def __ordered_drones(self, world_state: WorldState) -> Iterable[Drone]:
        return sorted(
            self.__drones,
            key=lambda drone: self.__drone_priority(drone, world_state),
            reverse=True,
        )

    def __drone_priority(
        self,
        drone: Drone,
        world_state: WorldState,
    ) -> tuple[int, float, int]:
        if drone.is_in_flight:
            return 2, 0.0, -drone.drone_id
        if drone.current_hub is None:
            return 0, 0.0, -drone.drone_id
        if drone.current_hub is self.__map.end_hub:
            return -1, 0.0, -drone.drone_id
        return (
            1,
            world_state.bottleneck_pressure(drone.current_hub),
            -drone.drone_id,
        )

    def __format_move(self, drone: Drone, hub: Hub) -> str:
        return f"D{drone.drone_id}-{hub.name}"

    @staticmethod
    def __build_hubs(fly_map: Map) -> Dict[str, Hub]:
        hubs: Dict[str, Hub] = {
            fly_map.start_hub.name: fly_map.start_hub,
            fly_map.end_hub.name: fly_map.end_hub,
        }
        hubs.update(fly_map.hubs)
        return hubs
