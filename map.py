from drone import Drone
from myregex import MapRegex
from mytypes import MapAttributes
from hub import StartHub, Hub, EndHub
from factorys import HubFactory, ConnectionFactory
from typing import Dict, List, Tuple, Generator, Optional
from exceptions import (
    MapFormatError, MapLogicError,
    ErrorInfo, NbDronesLineInspector,
)


class MapParser:
    """
    Parses a map file to extract configuration and map components.

    Reads the drone count, hubs, and connections from the specified file.
    """
    def __init__(self, map_path: str) -> None:
        """
        Initializes the MapParser with the file path.

        Args:
            map_path (str): The file path to the map configuration file.
        """
        with open(map_path, 'r') as file:
            self.__content = file.readlines()
        self.h_factory = HubFactory()
        self.c_factory = ConnectionFactory()

    def __lines(
        self,
    ) -> Generator[Tuple[int, str], None, None]:
        """
        Yields non-empty lines from the map file along with their line numbers.

        Strips comments and ignores empty lines. Yields (-1, "") at the end of the file.

        Yields:
            Tuple[int, str]: A tuple containing the line number and the line content.
        """
        for line_number, line in enumerate(
            self.__content, 1,
        ):
            line = line.split('#')[0].strip()
            if line:
                yield line_number, line
        yield -1, ""

    def parse(self) -> MapAttributes:
        """
        Parses the map file content into map attributes.

        Returns:
            MapAttributes: A tuple containing the number of drones, the start hub,
                a dictionary of normal hubs, and the end hub.

        Raises:
            MapFormatError: If there's a syntax or formatting error in the map file.
            MapLogicError: If there's a logical error in the map definition (e.g. duplicate names).
        """
        all_hubs: Dict[str, Hub] = dict()
        start_hub: Optional[StartHub] = None
        hubs: Dict[str, Hub] = dict()
        end_hub: Optional[EndHub] = None

        lines = self.__lines()
        n, line = next(lines)

        if n == -1:
            raise MapFormatError(ErrorInfo(
                line_number=0,
                line_content="",
                error_start=0,
                error_end=0,
                reason=(
                    "the file is empty or has only a commend and empty lines"
                ),
                expected="nb_drones: <positive integer>",
                how_to_fix="add a nb_drones line as the first entry"
                ),
            )

        match = MapRegex.NB_DRONS.match(line)

        if not match:
            raise MapFormatError(
                NbDronesLineInspector.inspect(line, n)
            )

        key = match.group('key')
        if key.lower() != 'nb_drones':
            raise MapFormatError(ErrorInfo(
                line_number=n,
                line_content=line,
                error_start=match.start('key'),
                error_end=match.end('key'),
                reason=(
                    f"'{key}' is not"
                    " the expected key"
                ),
                expected=(
                    "nb_drones as the first line key"
                ),
                how_to_fix=(
                    "rename the key to nb_drones"
                ),
            ))

        value_str = match.group('value')
        try:
            nb_drones = int(value_str)
        except (ValueError, TypeError):
            raise MapFormatError(ErrorInfo(
                line_number=n,
                line_content=line,
                error_start=match.start('value'),
                error_end=match.end('value'),
                reason=(
                    f"'{value_str}' is not"
                    " a valid integer"
                ),
                expected=(
                    "a positive integer"
                    " for drone count"
                ),
                how_to_fix=(
                    "replace the value with"
                    " a positive integer"
                ),
            ))

        if nb_drones <= 0:
            raise MapFormatError(ErrorInfo(
                line_number=n,
                line_content=line,
                error_start=match.start('value'),
                error_end=match.end('value'),
                reason=(
                    f"'{nb_drones}' is not"
                    " a positive value"
                ),
                expected=(
                    "a positive integer"
                    " greater than 0"
                ),
                how_to_fix=(
                    "use a positive number"
                    " for drone count"
                ),
            ))

        for n, line in lines:
            if n == -1:
                break

            if line.lstrip().lower().startswith(
                "connection"
            ):
                self.c_factory.create(
                    line, all_hubs, n,
                )
            else:
                hub = self.h_factory.create(
                    line, nb_drones, n,
                )

                if hub.name in all_hubs:
                    raise MapLogicError(ErrorInfo(
                        line_number=n,
                        line_content=line,
                        error_start=0,
                        error_end=len(line),
                        reason=(
                            f"hub '{hub.name}'"
                            " is already defined"
                        ),
                        expected=(
                            "each hub to have"
                            " a unique name"
                        ),
                        how_to_fix=(
                            "rename or remove the"
                            f" duplicate hub"
                            f" '{hub.name}'"
                        ),
                    ))

                if isinstance(hub, StartHub):
                    if start_hub is not None:
                        raise MapLogicError(ErrorInfo(
                            line_number=n,
                            line_content=line,
                            error_start=0,
                            error_end=len(line),
                            reason=(
                                "a start hub is"
                                " already defined"
                            ),
                            expected=(
                                "only one start hub"
                                " in the map"
                            ),
                            how_to_fix=(
                                "remove this duplicate"
                                " start hub"
                            ),
                        ))
                    start_hub = hub
                elif isinstance(hub, EndHub):
                    if end_hub is not None:
                        raise MapLogicError(ErrorInfo(
                            line_number=n,
                            line_content=line,
                            error_start=0,
                            error_end=len(line),
                            reason=(
                                "an end hub is"
                                " already defined"
                            ),
                            expected=(
                                "only one end hub"
                                " in the map"
                            ),
                            how_to_fix=(
                                "remove this duplicate"
                                " end hub"
                            ),
                        ))
                    end_hub = hub
                else:
                    hubs[hub.name] = hub

                all_hubs[hub.name] = hub

        if not start_hub:
            raise MapLogicError(ErrorInfo(
                line_number=0,
                line_content="",
                error_start=0,
                error_end=0,
                reason=(
                    "no start hub is"
                    " defined in the map"
                ),
                expected="exactly one start_hub line",
                how_to_fix=(
                    "add a start_hub line to the map"
                ),
            ))

        if not end_hub:
            raise MapLogicError(ErrorInfo(
                line_number=0,
                line_content="",
                error_start=0,
                error_end=0,
                reason=(
                    "no end hub is"
                    " defined in the map"
                ),
                expected="exactly one end_hub line",
                how_to_fix=(
                    "add an end_hub line to the map"
                ),
            ))

        return nb_drones, start_hub, hubs, end_hub


class Map:
    """
    Represents the simulated map.

    Contains the start hub, end hub, intermediate hubs, and the fleet of drones.
    """
    def __init__(self, map_path: str) -> None:
        """
        Initializes the Map by parsing the given map file.

        Args:
            map_path (str): The file path to the map configuration file.
        """
        self.__nb_drones: int
        self.__start_hub: StartHub
        self.__hubs: Dict[str, Hub]
        self.__end_hub: EndHub

        (
            self.__nb_drones,
            self.__start_hub,
            self.__hubs,
            self.__end_hub,
        ) = MapParser(map_path).parse()

        self.__drones: List[Drone] = [
            Drone(i, self.__start_hub)
            for i in range(1, self.__nb_drones + 1)
        ]

    @property
    def nb_drones(self) -> int:
        """int: The number of drones configured for this map."""
        return self.__nb_drones

    @property
    def start_hub(self) -> StartHub:
        """StartHub: The starting hub for all drones."""
        return self.__start_hub

    @property
    def hubs(self) -> Dict[str, Hub]:
        """Dict[str, Hub]: A dictionary of intermediate and priority hubs mapped by their names."""
        return self.__hubs

    @property
    def end_hub(self) -> EndHub:
        """EndHub: The destination hub for all drones."""
        return self.__end_hub

    @property
    def drones(self) -> List[Drone]:
        """List[Drone]: The list of drones initialized for the simulation."""
        return self.__drones
