from map import Map
from sys import argv
from engine import SimulationEngine


def main() -> None:
    map = Map(argv[1])
    engine = SimulationEngine(map)
    for n, turn in enumerate(engine.solution_generator()):
        print(f"{n}: {turn}")


if __name__ == "__main__":
    main()
