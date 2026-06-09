from zone import Zone
from typing import Dict
from abc import ABC, abstractmethod
from hub import StartHub, Hub, EndHub, HubParser
from connection import Connection, ConnectionParser
from exceptions import HubParsingError, ConnectionParsingError


class ZoneFactory(ABC):

    @abstractmethod
    def create(self, line: str) -> Zone:
        pass


class HubFactory(ZoneFactory):

    def __init__(self) -> None:
        self.__parser = HubParser()
        self.__seen: set[tuple[int, int]] = set()

    def create(self, line: str) -> Hub:
        _type, name, x, y, metadata = self.__parser.parse(line)

        if (x, y) in self.__seen:
            raise HubParsingError(line=line)

        self.__seen.add((x, y))

        if _type == "start_hub":
            return StartHub(name, x, y, metadata)
        if _type == "hub":
            return Hub(name, x, y, metadata)
        if _type == "end_hub":
            return EndHub(name, x, y, metadata)
        raise HubParsingError(line=line)


class ConnectionFactory:

    def __init__(self) -> None:
        self.__parser = ConnectionParser()
        self.__seen: set[frozenset[str]] = set()

    def create(self, line: str, zones: Dict[str, Zone]) -> None:
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

        zones[zone_from].connect(Connection(zone_to, max_link_capacity))
        zones[zone_to].connect(Connection(zone_from, max_link_capacity))
