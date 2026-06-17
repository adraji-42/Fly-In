from map import Map
from sys import argv
from simulation import Simulation


def main() -> None:
    map = Map(argv[1])
    engine = Simulation(map)
    for turn, output in enumerate(engine.run(), 1):
        print(f"{turn} {output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
