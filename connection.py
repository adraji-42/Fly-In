from mytyping import ConnectionAttribut
from regex import ConnectionRegex, ZoneRegex
from exceptions import (
    ConnectionParsingError,
    ConnectionMetaDataParsingError
)



class ConnectionParser:

    class ConnectionMetaDataParser:

        @staticmethod
        def parse(
            line: str, metadata_str: str
        ) -> int:
            match = ConnectionRegex.CONNECTION_METADATA.match(metadata_str)

            if not match:
                raise ConnectionMetaDataParsingError()

            if match.group("key") != "max_link_capacity":
                raise ConnectionMetaDataParsingError()

            try:
                max_link_capacity = int(match.group("value"))
                if max_link_capacity <= 0:
                    raise ConnectionMetaDataParsingError()
                return max_link_capacity
            except ValueError:
                raise ConnectionMetaDataParsingError()

    def parse(self, line: str) -> ConnectionAttribut:
        match = ConnectionRegex.CONNECTION_LINE.match(line)

        if not match:
            raise ConnectionParsingError()

        zone1, zone2 = match.group("zone1"), match.group("zone2")
        if not ZoneRegex.ZONE_NAME.match(zone2):
            raise ConnectionParsingError()

        max_link_capacity = 1
        metadata_str = match.group("metadata")
        if metadata_str is not None:
            if not metadata_str.strip():
                raise ConnectionMetaDataParsingError()
            else:
                max_link_capacity = self.ConnectionMetaDataParser.parse(line, metadata_str.strip())

        return zone1, zone2, max_link_capacity


class Connection:
    def __init__(
        self, zone_to: str, max_link_capacity: int = 1
    ) -> None:
        self.__zone_to = zone_to
        self.__max_link_capacity = max_link_capacity

    @property
    def zone_to(self) -> str:
        return self.__zone_to

    @property
    def max_link_capacity(self) -> int:
        return self.__max_link_capacity

    def __str__(self) -> str:
        return f"Connection to {self.zone_to} " \
               f"with max link capacity {self.max_link_capacity}"
