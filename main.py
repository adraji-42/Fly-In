from .map import Map
from sys import argv
from .simulation import Simulation


def main() -> None:
    map = Map(argv[1])
    engine = Simulation(map)
    engine.run()


if __name__ == "__main__":
    main()
