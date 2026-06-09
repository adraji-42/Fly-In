from abc import ABC, abstractmethod
from typing import Any, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection


class ZoneParser(ABC):

    @abstractmethod
    def parse(self, line: str) -> Any:
        ...


class Zone:

    def __init__(self, name: str, x: int, y: int) -> None:
        self.__name = name
        self.__x = x
        self.__y = y
        self.__connections: Set["Connection"] = set()

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
    def connections(self) -> set["Connection"]:
        return self.__connections

    def connect(self, connection: "Connection") -> None:
        self.__connections.add(connection)
