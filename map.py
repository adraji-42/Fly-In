from regex import MapRegex
from mytyping import MapAttributes
from hub import StartHub, Hub, EndHub
from typing import List, Dict, Optional
from factorys import HubFactory, ConnectionFactory
from exceptions import MapParsingError, ConnectionError, HubError


class MapParser:
    def __init__(self, map_path):
        with open(map_path, 'r') as file:
            self.__content = file.readlines()
        self.h_factory = HubFactory()
        self.c_factory = ConnectionFactory()

    def parse(self) -> MapAttributes:
        all_hubs: Dict[str, Hub] = dict()
        start_hub: Optional[StartHub] = None
        hubs: Dict[str, Hub] = dict()
        end_hub: Optional[EndHub] = None

        nb_drones = None

        for n, line in enumerate(self.__content, 1):
            if '#' in line:
                if not (line := line.split('#')[0].strip()):
                    continue
            elif not line.strip():
                continue

            match = MapRegex.NB_DRONS.match(line)

            if not match:
                raise MapParsingError(line=line, line_number=n)

            if match.group('key').lower() != 'nb_drones':
                raise MapParsingError(line=line, line_number=n)

            try:
                nb_drones = int(match.group('value'))
                if nb_drones < 0:
                    raise MapParsingError(line=line, line_number=n)
                elif nb_drones == 0:
                    raise MapParsingError(line=line, line_number=n)
            except ValueError as error:
                raise MapParsingError(
                    line=line, line_number=n, original=error
                ) from error

            break

        if nb_drones is None:
            raise MapParsingError()

        for n, line in enumerate(self.__content[n:], n + 1):
            if '#' in line:
                if not (line := line.split('#')[0].strip()):
                    continue
            elif not line.strip():
                continue

            if line.lstrip().lower().startswith("connection"):
                try:
                    self.c_factory.create(line, all_hubs)
                except ConnectionError as error:
                    raise MapParsingError(
                        line=line, line_number=n, original=error
                    ) from error
            else:
                try:
                    hub = self.h_factory.create(line)

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
            raise MapParsingError()
        if not end_hub:
            raise MapParsingError()

        return nb_drones, start_hub, hubs, end_hub


class Map:
    def __init__(self, map_path: str):
        self.nb_drones: int
        self.start_hub: StartHub
        self.hubs: List[Hub]
        self.end_hub: EndHub
        self.nb_drones, self.start_hub, self.hubs, self.end_hub = MapParser(
            map_path
        ).parse()
