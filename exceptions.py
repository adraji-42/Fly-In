from enum import StrEnum
from typing import Tuple, Callable


GET_BAD_POSITION: Callable[[str, str], Tuple[int, int]] = lambda line, part: (
    pos := line.find(part.strip()),
    pos + len(part.strip())
)


class Color(StrEnum):
    RED = "\033[31m"
    RED_BG = "\033[41m"
    RESET = "\033[0m"


class MapError(Exception):
    ...


class MapParsingError(MapError):
    ...


class HubError(MapError):
    ...


class HubParsingError(HubError, MapParsingError):
    ...


class HubMetaDataParsingError(HubParsingError):
    ...


class ConnectionError(MapError):
    ...


class ConnectionParsingError(ConnectionError, MapParsingError):
    ...


class ConnectionMetaDataParsingError(ConnectionParsingError):
    ...
