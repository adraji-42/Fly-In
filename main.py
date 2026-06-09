from map import Map
from simulation_engine import SimulationEngine
from sys import argv


def main() -> None:
    fly_map = Map(argv[1])
    engine = SimulationEngine(fly_map)

    for turn in engine.run():
        print(" ".join(turn))


if __name__ == "__main__":
    main()
