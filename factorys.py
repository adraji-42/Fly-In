from zone import Zone
from typing import Dict
from abc import ABC, abstractmethod
from exceptions import ConnectionError
from connection import Connection, ConnectionParser
from hub import StartHub, Hub, EndHub, HubParser


class ZoneFactory(ABC):

    @abstractmethod
    def create(self, line: str) -> Zone:
        pass


class HubFactory(ZoneFactory):

    def __init__(self) -> None:
        self.__parser = HubParser()

    def create(self, line: str) -> Hub:
        _type, *args = self.__parser.parse(line)
        if _type == "start_hub":
            return StartHub(*args)
        if _type == "hub":
            return Hub(*args)
        if _type == "end_hub":
            return EndHub(*args)


class ConnectionFactory:

    def __init__(self) -> None:
        self.__parser = ConnectionParser()

    def create(self, line: str, zones: Dict[str, Zone]) -> None:
        zone_from, zone_to, max_link_capacity = self.__parser.parse(line)

        if zone_from not in zones:
            raise ConnectionError()
        if zone_to not in zones:
            raise ConnectionError()

        zones[zone_from].connect(Connection(zone_to, max_link_capacity))
