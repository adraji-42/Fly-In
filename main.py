from map import Map
from sys import argv
from engine import SimulationEngine


def main() -> None:
    map = Map(argv[1])
    engine = SimulationEngine(map)
    for move in engine.soulation_generator():
        print(move)


if __name__ == "__main__":
    main()
