from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection


class ZoneParser(ABC):

    @abstractmethod
    def parse(self, line: str, line_number: int) -> Any:
        ...


class Zone:

    def __init__(self, name: str, x: int, y: int) -> None:
        self.__name = name
        self.__x = x
        self.__y = y
        self.__connections: Dict[str, "Connection"] = {}

    @property
    def name(self) -> str:
        return self.__name

    @property
    def x(self) -> int:
        return self.__x

    @property
    def y(self) -> int:
        return self.__y

    @property
    def connections(self) -> Dict[str, "Connection"]:
        return self.__connections

    def connect(self, connection: "Connection") -> None:
        self.__connections[connection.hub_to.name] = connection
