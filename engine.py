from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Dict, Generator, Iterator, List, Optional, Tuple

from drone import Drone, MovementEvent
from hub import Hub, StartHub
from map import Map
from path import Path, PathFinder, PathStep


State = Tuple[int, int]
Previous = Dict[State, Tuple[State, "ScheduleAction"]]
TurnQueue = List[Tuple[int, int, int]]


@dataclass(frozen=True)
class ScheduleAction:
    kind: str
    hub: Hub
    turn: int
    step: Optional[PathStep] = None
    arrival_turn: Optional[int] = None


class ReservationTable:
    def __init__(self) -> None:
        self.__hub_usage: Dict[Tuple[str, int], int] = {}
        self.__link_usage: Dict[Tuple[Tuple[str, str], int], int] = {}
        self.__latest_turn = 0

    @property
    def latest_turn(self) -> int:
        return self.__latest_turn

    def can_reserve_hub(self, hub: Hub, turn: int) -> bool:
        if isinstance(hub, StartHub):
            return True
        return self.__hub_usage.get((hub.name, turn), 0) < hub.max_drones

    def can_reserve_link(self, step: PathStep, turn: int) -> bool:
        key = step.edge_key, turn
        usage = self.__link_usage.get(key, 0)
        return usage < step.connection.max_link_capacity

    def reserve_hub(self, hub: Hub, turn: int) -> None:
        if isinstance(hub, StartHub):
            return
        key = hub.name, turn
        self.__hub_usage[key] = self.__hub_usage.get(key, 0) + 1
        self.__latest_turn = max(self.__latest_turn, turn)

    def reserve_link(self, step: PathStep, turn: int) -> None:
        key = step.edge_key, turn
        self.__link_usage[key] = self.__link_usage.get(key, 0) + 1
        self.__latest_turn = max(self.__latest_turn, turn)


class DronePlan:
    def __init__(
        self,
        path: Path,
        actions: List[ScheduleAction],
        arrival_turn: int,
    ) -> None:
        self.__path = path
        self.__actions = actions
        self.__arrival_turn = arrival_turn
        self.__events: List[MovementEvent] = []

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def arrival_turn(self) -> int:
        return self.__arrival_turn

    @property
    def events(self) -> List[MovementEvent]:
        return self.__events

    def commit(self, table: ReservationTable) -> None:
        for action in self.__actions:
            if action.kind == "wait":
                table.reserve_hub(action.hub, action.turn)
                continue
            if action.step is None or action.arrival_turn is None:
                continue
            table.reserve_link(action.step, action.turn)
            table.reserve_hub(action.step.destination, action.arrival_turn)
            if action.step.travel_time == 2:
                self.__events.append(
                    MovementEvent(action.turn, action.step.connection_name)
                )
                self.__events.append(
                    MovementEvent(
                        action.arrival_turn,
                        action.step.destination.name,
                    )
                )
            else:
                self.__events.append(
                    MovementEvent(
                        action.arrival_turn,
                        action.step.destination.name,
                    )
                )


class PathPlanner:
    def __init__(
        self,
        table: ReservationTable,
        nb_drones: int,
    ) -> None:
        self.__table = table
        self.__nb_drones = nb_drones

    def plan(self, path: Path) -> DronePlan:
        max_turn = (
            self.__table.latest_turn
            + path.base_cost
            + self.__nb_drones
            + len(path.hubs)
            + 5
        )
        while True:
            plan = self.__search(path, max_turn)
            if plan is not None:
                return plan
            max_turn *= 2

    def __search(self, path: Path, max_turn: int) -> Optional[DronePlan]:
        unique = count()
        queue: TurnQueue = []
        start_state: State = (0, 0)
        previous: Previous = {}
        best_times: Dict[State, int] = {start_state: 0}
        heappush(queue, (0, 0, next(unique)))

        while queue:
            time, index, _ = heappop(queue)
            state = index, time
            if best_times.get(state) != time:
                continue
            if index == len(path.steps):
                return self.__build_plan(path, previous, state)
            if time >= max_turn:
                continue

            self.__push_wait(
                path,
                state,
                previous,
                best_times,
                queue,
                unique,
                max_turn,
            )
            self.__push_move(
                path,
                state,
                previous,
                best_times,
                queue,
                unique,
                max_turn,
            )

        return None

    def __push_wait(
        self,
        path: Path,
        state: State,
        previous: Previous,
        best_times: Dict[State, int],
        queue: TurnQueue,
        unique: Iterator[int],
        max_turn: int,
    ) -> None:
        index, time = state
        hub = path.hubs[index]
        wait_turn = time + 1
        next_state = index, wait_turn
        if wait_turn > max_turn:
            return
        if not self.__table.can_reserve_hub(hub, wait_turn):
            return
        if best_times.get(next_state, max_turn + 1) <= wait_turn:
            return
        best_times[next_state] = wait_turn
        previous[next_state] = (
            state,
            ScheduleAction("wait", hub, wait_turn),
        )
        heappush(queue, (wait_turn, index, next(unique)))

    def __push_move(
        self,
        path: Path,
        state: State,
        previous: Previous,
        best_times: Dict[State, int],
        queue: TurnQueue,
        unique: Iterator[int],
        max_turn: int,
    ) -> None:
        index, time = state
        step = path.steps[index]
        departure_turn = time + 1
        arrival_turn = departure_turn + step.travel_time - 1
        next_state = index + 1, arrival_turn
        if arrival_turn > max_turn:
            return
        if not self.__table.can_reserve_link(step, departure_turn):
            return
        if not self.__table.can_reserve_hub(step.destination, arrival_turn):
            return
        if best_times.get(next_state, max_turn + 1) <= arrival_turn:
            return
        best_times[next_state] = arrival_turn
        previous[next_state] = (
            state,
            ScheduleAction(
                "move",
                step.source,
                departure_turn,
                step,
                arrival_turn,
            ),
        )
        heappush(queue, (arrival_turn, index + 1, next(unique)))

    def __build_plan(
        self,
        path: Path,
        previous: Previous,
        end_state: State,
    ) -> DronePlan:
        state = end_state
        actions: List[ScheduleAction] = []
        while state in previous:
            state, action = previous[state]
            actions.append(action)
        actions.reverse()
        return DronePlan(path, actions, end_state[1])


class DroneScheduler:
    def __init__(self, paths: List[Path], nb_drones: int) -> None:
        if not paths:
            raise ValueError("No viable paths found in the map.")
        self.__paths = paths
        self.__table = ReservationTable()
        self.__planner = PathPlanner(self.__table, nb_drones)

    def schedule(self, drone: Drone) -> None:
        plans = [self.__planner.plan(path) for path in self.__paths]
        best = min(
            plans,
            key=lambda plan: (
                plan.arrival_turn,
                plan.path.base_cost,
                plan.path.priority_score,
                len(plan.path.hubs),
            ),
        )
        best.commit(self.__table)
        drone.assign_plan(best.path, best.events, best.arrival_turn)


class SimulationEngine:
    def __init__(self, fly_map: Map) -> None:
        self.__drones = [
            Drone(index, fly_map.start_hub)
            for index in range(1, fly_map.nb_drones + 1)
        ]
        paths = PathFinder.find_paths(fly_map.start_hub, fly_map.nb_drones)
        self.__scheduler = DroneScheduler(paths, fly_map.nb_drones)
        for drone in self.__drones:
            self.__scheduler.schedule(drone)

    @property
    def all_finished(self) -> bool:
        return all(drone.finished for drone in self.__drones)

    def solution_generator(self) -> Generator[str, None, None]:
        events_by_turn: Dict[int, List[str]] = {}
        for drone in self.__drones:
            for event in drone.events:
                events_by_turn.setdefault(event.turn, []).append(
                    f"D{drone.id}-{event.token}"
                )
        for turn in sorted(events_by_turn):
            yield " ".join(events_by_turn[turn])
