from hub import Hub
from mytypes import ConnectionAttribute
from regex import ConnectionRegex
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
                raise ConnectionMetaDataParsingError(
                    line=line,
                    metadata=metadata_str,
                )

            if match.group("key") != "max_link_capacity":
                raise ConnectionMetaDataParsingError(
                    line=line,
                    metadata=metadata_str,
                )

            try:
                max_link_capacity = int(match.group("value"))
                if max_link_capacity <= 0:
                    raise ConnectionMetaDataParsingError(
                        line=line,
                        metadata=metadata_str,
                    )
                return max_link_capacity
            except ValueError:
                raise ConnectionMetaDataParsingError(
                    line=line,
                    metadata=metadata_str,
                )

    def parse(self, line: str) -> ConnectionAttribute:
        match = ConnectionRegex.CONNECTION_LINE.match(line)

        if not match:
            raise ConnectionParsingError(line=line)

        zone1, zone2 = match.group("zone1"), match.group("zone2")
        max_link_capacity = 1
        metadata_str = match.group("metadata")
        if metadata_str is not None:
            if not metadata_str.strip():
                raise ConnectionMetaDataParsingError(
                    line=line,
                    metadata=metadata_str,
                )
            else:
                max_link_capacity = self.ConnectionMetaDataParser.parse(
                    line,
                    metadata_str.strip(),
                )

        return zone1, zone2, max_link_capacity


class Connection:
    def __init__(
        self, hub_to: Hub, max_link_capacity: int = 1
    ) -> None:
        self.__hub_to: Hub = hub_to
        self.__max_link_capacity: int = max_link_capacity

    @property
    def hub_to(self) -> Hub:
        return self.__hub_to

    @property
    def max_link_capacity(self) -> int:
        return self.__max_link_capacity
