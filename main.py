from map import Map
from sys import argv


def main() -> None:
    map = Map(argv[1])
    print(f"nb_drones: {map.nb_drones}")
    print(f"\nstart_hub: {map.start_hub}")
    for connection in map.start_hub.connections:
        print(f"\t{map.start_hub.name} {connection}")

    for hub in map.hubs.values():
        print(f"\nHub: {hub}")
        for connection in hub.connections:
            print(f"\t{hub.name} {connection}")

    print(f"\nend_hub: {map.end_hub}")
    for connection in map.end_hub.connections:
        print(f"\t{map.end_hub.name} {connection}")


if __name__ == "__main__":
    main()
