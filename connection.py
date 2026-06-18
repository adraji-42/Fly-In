from re import Match
from hub import Hub
from typing import Dict, Optional
from mytypes import ConnectionAttribute
from myregex import ConnectionRegex
from exceptions import (
    MapFormatError, ErrorInfo,
    ConnectionLineInspector,
    ConnectionMetadataInspector,
)


class ConnectionParser:

    class ConnectionMetaDataParser:

        @staticmethod
        def parse(
            line: str, metadata_str: str,
            line_number: int, metadata_offset: int,
        ) -> int:
            match = ConnectionRegex.CONNECTION_METADATA.match(
                metadata_str
            )

            if not match:
                raise MapFormatError(
                    ConnectionMetadataInspector.inspect(
                        line, metadata_str,
                        line_number, metadata_offset,
                    )
                )

            key = match.group("key")
            value = match.group("value")
            key_pos = line.find(key, metadata_offset)
            val_pos = line.find(
                value, key_pos + len(key)
            )

            if key != "max_link_capacity":
                raise MapFormatError(ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=key_pos,
                    error_end=key_pos + len(key),
                    reason=(
                        f"'{key}' is not a valid"
                        " connection metadata key"
                    ),
                    expected="max_link_capacity",
                    how_to_fix=(
                        "rename the key"
                        " to max_link_capacity"
                    ),
                ))

            try:
                capacity = int(value)
            except ValueError:
                raise MapFormatError(ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=val_pos,
                    error_end=val_pos + len(value),
                    reason=(
                        f"'{value}' is not"
                        " a valid integer"
                    ),
                    expected="a positive integer",
                    how_to_fix=(
                        "replace with a positive integer"
                    ),
                ))

            if capacity <= 0:
                raise MapFormatError(ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=val_pos,
                    error_end=val_pos + len(value),
                    reason=(
                        f"'{value}' must be"
                        " greater than 0"
                    ),
                    expected=(
                        "a positive integer"
                        " greater than 0"
                    ),
                    how_to_fix=(
                        "use a number greater than 0"
                    ),
                ))

            return capacity

    def parse(
        self, line: str, line_number: int,
    ) -> ConnectionAttribute:
        match: Optional[Match[str]] = (
            ConnectionRegex.CONNECTION_LINE.match(line)
        )

        if not match:
            raise MapFormatError(
                ConnectionLineInspector.inspect(
                    line, line_number,
                )
            )

        zone1 = match.group("zone1")
        zone2 = match.group("zone2")
        max_link_capacity = 1
        metadata_str = match.group("metadata")

        if metadata_str is not None:
            if not metadata_str.strip():
                bracket_start = line.find("[")
                bracket_end = line.find(
                    "]", bracket_start,
                ) + 1
                raise MapFormatError(ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=bracket_start,
                    error_end=bracket_end,
                    reason=(
                        "the metadata block is empty"
                    ),
                    expected=(
                        "max_link_capacity="
                        "<positive integer>"
                        " or no brackets"
                    ),
                    how_to_fix=(
                        "remove empty brackets"
                        " or add metadata"
                    ),
                ))
            else:
                raw = metadata_str
                stripped = raw.strip()
                leading = len(raw) - len(raw.lstrip())
                m_offset = (
                    match.start("metadata") + leading
                )
                max_link_capacity = (
                    self.ConnectionMetaDataParser.parse(
                        line, stripped,
                        line_number, m_offset,
                    )
                )

        return zone1, zone2, max_link_capacity


class Connection:
    def __init__(
        self, hub_from: Hub, hub_to: Hub,
        max_link_capacity: int = 1,
    ) -> None:
        self.__hub_from: str = str(hub_from)
        self.__hub_to: Hub = hub_to
        self.__max_link_capacity: int = max_link_capacity
        self.__reservations: Dict[int, int] = {}

    @property
    def hub_from(self) -> str:
        return self.__hub_from

    @property
    def hub_to(self) -> Hub:
        return self.__hub_to

    @property
    def max_link_capacity(self) -> int:
        return self.__max_link_capacity

    def can_reserve(self, time: int) -> bool:
        return (
            self.__reservations.get(time, 0)
            < self.__max_link_capacity
        )

    def reserve(self, time: int) -> bool:
        if not self.can_reserve(time):
            return False
        self.__reservations[time] = (
            self.__reservations.get(time, 0) + 1
        )
        return True

    def nearest_reservation(
        self, start_time: int,
    ) -> int:
        time = start_time
        while not self.can_reserve(time):
            time += 1
        return time

    def __str__(self) -> str:
        return f"{self.__hub_from}-{self.__hub_to}"
