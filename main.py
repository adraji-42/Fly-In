from map import Map
from sys import argv
from simulation import Simulation
from exceptions import BaseMapProjectError


def main() -> None:
    map = Map(argv[1])
    engine = Simulation(map)
    for turn, output in enumerate(engine.run(), 1):
        print(f"{turn} {output}")


if __name__ == "__main__":
    try:
        main()
    except BaseMapProjectError as e:
        print(e)
    except Exception as e:
        print(f"Error: {e}")
