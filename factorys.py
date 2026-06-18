from typing import Dict, Callable
from hub import StartHub, Hub, EndHub, HubParser
from connection import Connection, ConnectionParser
from exceptions import MapLogicError, ErrorInfo


class HubFactory:

    def __init__(self) -> None:
        self.__parser = HubParser()
        self.__seen: set[tuple[int, int]] = set()

    def create(
        self, line: str,
        nb_drones: int, line_number: int,
    ) -> Hub:
        _type, name, x, y, metadata = (
            self.__parser.parse(line, line_number)
        )

        if (x, y) in self.__seen:
            raise MapLogicError(ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    f"coordinates ({x}, {y}) are"
                    " already used by another hub"
                ),
                expected=(
                    "each hub to have"
                    " unique coordinates"
                ),
                how_to_fix=(
                    "change the coordinates"
                    " to unused values"
                ),
            ))

        self.__seen.add((x, y))

        builders: Dict[str, Callable[[], Hub]] = {
            "start_hub": lambda: StartHub(
                name, x, y, nb_drones, metadata,
            ),
            "hub": lambda: Hub(
                name, x, y, metadata,
            ),
            "end_hub": lambda: EndHub(
                name, x, y, nb_drones, metadata,
            ),
        }
        return builders[_type]()


class ConnectionFactory:

    def __init__(self) -> None:
        self.__parser = ConnectionParser()
        self.__seen: set[frozenset[str]] = set()

    def create(
        self, line: str,
        zones: Dict[str, Hub], line_number: int,
    ) -> None:
        zone1, zone2, max_link_capacity = (
            self.__parser.parse(line, line_number)
        )

        if zone1 == zone2:
            raise MapLogicError(ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    f"hub '{zone1}' cannot"
                    " connect to itself"
                ),
                expected=(
                    "a connection between"
                    " two different hubs"
                ),
                how_to_fix=(
                    "use two different hub names"
                ),
            ))

        if zone1 not in zones:
            raise MapLogicError(ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    f"the hub {zone1} in the"
                    " connection is not defined"
                ),
                expected=(
                    "link between two hub"
                    " defined before this line"
                ),
                how_to_fix=(
                    f"remove this line or define"
                    f" hub {zone1} before this line"
                ),
            ))

        if zone2 not in zones:
            raise MapLogicError(ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    f"the hub {zone2} in the"
                    " connection is not defined"
                ),
                expected=(
                    "link between two hub"
                    " defined before this line"
                ),
                how_to_fix=(
                    f"remove this line or define"
                    f" hub {zone2} before this line"
                ),
            ))

        pair = frozenset({zone1, zone2})
        if pair in self.__seen:
            raise MapLogicError(ErrorInfo(
                line_number=line_number,
                line_content=line,
                error_start=0,
                error_end=len(line),
                reason=(
                    f"connection between '{zone1}'"
                    f" and '{zone2}'"
                    " is already defined"
                ),
                expected=(
                    "each connection to be"
                    " defined only once"
                ),
                how_to_fix=(
                    "remove this duplicate connection"
                ),
            ))
        self.__seen.add(pair)

        zones[zone1].connect(
            Connection(
                zones[zone1], zones[zone2],
                max_link_capacity,
            )
        )
        zones[zone2].connect(
            Connection(
                zones[zone2], zones[zone1],
                max_link_capacity,
            )
        )
