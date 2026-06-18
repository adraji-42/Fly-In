from drone import Drone
from myregex import MapRegex
from mytypes import MapAttributes
from hub import StartHub, Hub, EndHub
from typing import Dict, List, Tuple, Iterator, Optional
from factorys import HubFactory, ConnectionFactory
from exceptions import MapParsingError, ConnectionError, HubError


class MapParser:
    def __init__(self, map_path: str) -> None:
        with open(map_path, 'r') as file:
            self.__content = file.readlines()
        if not self.__content:
            raise MapParsingError("Map file is empty")
        self.h_factory = HubFactory()
        self.c_factory = ConnectionFactory()

    def __lines(self) -> Iterator[Tuple[int, str]]:
        for line_number, line in enumerate(self.__content, 1):
            line = line.split('#')[0].strip()
            if line:
                yield line_number, line

    def parse(self) -> MapAttributes:
        all_hubs: Dict[str, Hub] = dict()
        start_hub: Optional[StartHub] = None
        hubs: Dict[str, Hub] = dict()
        end_hub: Optional[EndHub] = None

        nb_drones = None
        lines = self.__lines()

        for n, line in lines:
            match = MapRegex.NB_DRONS.match(line)

            if not match:
                raise MapParsingError(line=line, line_number=n)

            if match.group('key').lower() != 'nb_drones':
                raise MapParsingError(line=line, line_number=n)

            try:
                nb_drones = int(match.group('value'))
                if nb_drones <= 0:
                    raise MapParsingError(line=line, line_number=n)
            except ValueError as error:
                raise MapParsingError(
                    line=line, line_number=n, original=error
                ) from error

            break

        if nb_drones is None:
            raise MapParsingError()

        for n, line in lines:
            if line.lstrip().lower().startswith("connection"):
                try:
                    self.c_factory.create(line, all_hubs)
                except ConnectionError as error:
                    raise MapParsingError(
                        line=line, line_number=n, original=error
                    ) from error
            else:
                try:
                    hub = self.h_factory.create(line, nb_drones)

                    if hub.name in all_hubs:
                        raise MapParsingError(line=line, line_number=n)

                    if isinstance(hub, StartHub):
                        if start_hub is not None:
                            raise MapParsingError(line=line, line_number=n)
                        start_hub = hub
                    elif isinstance(hub, EndHub):
                        if end_hub is not None:
                            raise MapParsingError(line=line, line_number=n)
                        end_hub = hub
                    else:
                        hubs[hub.name] = hub

                    all_hubs[hub.name] = hub
                except HubError as error:
                    raise MapParsingError(
                        line=line, line_number=n, original=error
                    ) from error

        if not start_hub:
            raise MapParsingError("Start hub is missing")
        if not end_hub:
            raise MapParsingError("End hub is missing")

        return nb_drones, start_hub, hubs, end_hub


class Map:
    def __init__(self, map_path: str):
        self.__nb_drones: int
        self.__start_hub: StartHub
        self.__hubs: Dict[str, Hub]
        self.__end_hub: EndHub

        self.__nb_drones, self.__start_hub, self.__hubs, self.__end_hub = (
            MapParser(map_path).parse()
        )

        self.__drones: List[Drone] = [
            Drone(i, self.__start_hub) for i in range(1, self.__nb_drones + 1)
        ]

    @property
    def nb_drones(self) -> int:
        return self.__nb_drones

    @property
    def start_hub(self) -> StartHub:
        return self.__start_hub

    @property
    def hubs(self) -> Dict[str, Hub]:
        return self.__hubs

    @property
    def end_hub(self) -> EndHub:
        return self.__end_hub

    @property
    def drones(self) -> List[Drone]:
        return self.__drones
