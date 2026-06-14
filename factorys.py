from typing import Dict
from hub import StartHub, Hub, EndHub, HubParser
from connection import Connection, ConnectionParser
from exceptions import HubParsingError, ConnectionParsingError


class HubFactory:

    def __init__(self) -> None:
        self.__parser = HubParser()
        self.__seen: set[tuple[int, int]] = set()

    def create(self, line: str, nb_drones: int) -> Hub:
        _type, name, x, y, metadata = self.__parser.parse(line)

        if (x, y) in self.__seen:
            raise HubParsingError(line=line)

        self.__seen.add((x, y))

        builders = {
            "start_hub": lambda: StartHub(name, x, y, nb_drones, metadata),
            "hub": lambda: Hub(name, x, y, metadata),
            "end_hub": lambda: EndHub(name, x, y, nb_drones, metadata),
        }
        return builders[_type]()


class ConnectionFactory:

    def __init__(self) -> None:
        self.__parser = ConnectionParser()
        self.__seen: set[frozenset[str]] = set()

    def create(self, line: str, zones: Dict[str, Hub]) -> None:
        zone_from, zone_to, max_link_capacity = self.__parser.parse(line)

        if zone_from == zone_to:
            raise ConnectionParsingError(line=line)

        if zone_from not in zones:
            raise ConnectionParsingError(line=line)
        if zone_to not in zones:
            raise ConnectionParsingError(line=line)

        pair = frozenset({zone_from, zone_to})
        if pair in self.__seen:
            raise ConnectionParsingError(line=line)
        self.__seen.add(pair)

        zones[zone_from].connect(Connection(zones[zone_to], max_link_capacity))
        zones[zone_to].connect(Connection(zones[zone_from], max_link_capacity))
