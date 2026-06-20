from map import Map
from sys import argv
from simulation import Simulation
from exceptions import BaseMapProjectError


def main() -> None:
    """
    Main entry point for the simulation program.

    Reads the map file path from command line arguments, initializes the Map
    and Simulation engine, and runs the simulation turn by turn, printing
    the output.
    """
    map = Map(argv[1])
    engine = Simulation(map)
    for turn, output in enumerate(engine.run(), 1):
        print(f"{output}")


if __name__ == "__main__":
    try:
        main()
    except BaseMapProjectError as e:
        print(e)
    except Exception as e:
        print(f"Error: {e}")
