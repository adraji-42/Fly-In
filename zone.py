from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

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
        self.connections: set["Connection"] = set()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def x(self) -> int:
        return self.__x

    @property
    def y(self) -> int:
        return self.__y

    def connect(self, connection: "Connection") -> None:
        self.connections.add(connection)
