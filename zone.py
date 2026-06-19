from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection


class ZoneParser(ABC):
    """
    Abstract base class for parsing zone definitions from the map file.
    """

    @abstractmethod
    def parse(self, line: str, line_number: int) -> Any:
        """
        Parses a line defining a zone.

        Args:
            line (str): The line content to parse.
            line_number (int): The current line number in the file.

        Returns:
            Any: The parsed zone attributes.
        """
        ...


class Zone:
    """
    Base class representing a physical location on the map.

    Attributes:
        name (str): The unique name of the zone.
        x (int): The x-coordinate.
        y (int): The y-coordinate.
    """

    def __init__(self, name: str, x: int, y: int) -> None:
        """
        Initializes a Zone.

        Args:
            name (str): The name of the zone.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
        """
        self.__name = name
        self.__x = x
        self.__y = y
        self.__connections: Dict[str, "Connection"] = {}

    @property
    def name(self) -> str:
        """str: The name of the zone."""
        return self.__name

    @property
    def x(self) -> int:
        """int: The x-coordinate of the zone."""
        return self.__x

    @property
    def y(self) -> int:
        """int: The y-coordinate of the zone."""
        return self.__y

    @property
    def connections(self) -> Dict[str, "Connection"]:
        """Dict[str, 'Connection']: The outbound connections from this zone mapped by destination name."""
        return self.__connections

    def connect(self, connection: "Connection") -> None:
        """
        Adds an outbound connection from this zone.

        Args:
            connection (Connection): The connection object to add.
        """
        self.__connections[connection.hub_to.name] = connection
