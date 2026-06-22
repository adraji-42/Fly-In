from re import Match
from hub import Hub
from typing import Dict, Optional
from mytypes import ConnectionAttribute, ConnectionMetaData
from myregex import ConnectionRegex, HubRegex
from exceptions import (
    MapFormatError,
    ErrorInfo,
    ConnectionLineInspector,
    ConnectionMetadataInspector,
)


class ConnectionParser:
    """
    Parser for connection definitions in the map file.

    Extracts connection attributes including the linked zones, capacity,
    and metadata.
    """

    class ConnectionMetaDataParser:
        """
        Sub-parser for handling the metadata block within a connection
        definition line.

        Parses one or more key=value pairs, mirroring the behaviour of
        HubParser.HubMetaDataParser. Returns a dict of all parsed attributes.
        The only currently supported key is ``max_link_capacity``.
        """

        @staticmethod
        def parse(
            line: str,
            metadata_str: str,
            line_number: int,
            metadata_offset: int,
        ) -> Dict[str, ConnectionMetaData]:
            """
            Parses all key=value pairs from a connection metadata block.

            Args:
                line (str): The original line from the map file.
                metadata_str (str): The extracted metadata string (content
                    inside brackets).
                line_number (int): The current line number in the file.
                metadata_offset (int): The character offset where metadata
                    begins in the line.

            Returns:
                Dict[str, ConnectionMetaData]: The parsed metadata key-value
                    pairs.

            Raises:
                MapFormatError: If the metadata format is invalid, contains
                    unknown keys, or contains invalid values.
            """
            if not ConnectionRegex.CONNECTION_METADATA.match(metadata_str):
                raise MapFormatError(
                    ConnectionMetadataInspector.inspect(
                        line,
                        metadata_str,
                        line_number,
                        metadata_offset,
                    )
                )

            metadata: Dict[str, ConnectionMetaData] = {}
            remaining = metadata_str.strip()
            search_from = metadata_offset

            while remaining:
                match = HubRegex.PAIRS_KV.match(remaining)
                if not match:
                    raise MapFormatError(
                        ConnectionMetadataInspector.inspect(
                            line,
                            metadata_str,
                            line_number,
                            metadata_offset,
                        )
                    )

                key = match.group("key").lower()
                value = match.group("value")
                key_pos = line.find(key, search_from)
                val_pos = line.find(value, key_pos + len(key))
                search_from = val_pos + len(value)
                remaining = remaining[match.end():].strip()

                if key == "max_link_capacity":
                    try:
                        capacity = int(value)
                    except ValueError:
                        raise MapFormatError(
                            ErrorInfo(
                                line_number=line_number,
                                line_content=line,
                                error_start=val_pos,
                                error_end=val_pos + len(value),
                                reason=(
                                    f"'{value}' is not a valid integer"
                                ),
                                expected="a positive integer",
                                how_to_fix=(
                                    "replace with a positive integer"
                                ),
                            )
                        )
                    if capacity <= 0:
                        raise MapFormatError(
                            ErrorInfo(
                                line_number=line_number,
                                line_content=line,
                                error_start=val_pos,
                                error_end=val_pos + len(value),
                                reason=(
                                    f"'{value}' must be greater than 0"
                                ),
                                expected=(
                                    "a positive integer greater than 0"
                                ),
                                how_to_fix=("use a number greater than 0"),
                            )
                        )
                    metadata[key] = capacity
                else:
                    raise MapFormatError(
                        ErrorInfo(
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
                                "rename the key to a supported"
                                " metadata key or remove it"
                            ),
                        )
                    )

            return metadata

    def parse(
        self,
        line: str,
        line_number: int,
    ) -> ConnectionAttribute:
        """
        Parses a full connection definition line.

        Args:
            line (str): The raw line string from the map file.
            line_number (int): The line number in the map file.

        Returns:
            ConnectionAttribute: A tuple containing zone1, zone2, and a dict
                of parsed metadata key-value pairs.

        Raises:
            MapFormatError: If the line format is invalid or missing required
                components.
        """
        match: Optional[Match[str]] = ConnectionRegex.CONNECTION_LINE.match(
            line
        )

        if not match:
            raise MapFormatError(
                ConnectionLineInspector.inspect(
                    line,
                    line_number,
                )
            )

        zone1 = match.group("zone1")
        zone2 = match.group("zone2")
        metadata: Dict[str, ConnectionMetaData] = {}
        metadata_str = match.group("metadata")

        if metadata_str is not None:
            if not metadata_str.strip():
                bracket_start = line.find("[")
                bracket_end = (
                    line.find(
                        "]",
                        bracket_start,
                    )
                    + 1
                )
                raise MapFormatError(
                    ErrorInfo(
                        line_number=line_number,
                        line_content=line,
                        error_start=bracket_start,
                        error_end=bracket_end,
                        reason=("the metadata block is empty"),
                        expected=(
                            "key=value pairs"
                            " or no brackets at all"
                        ),
                        how_to_fix=(
                            "remove empty brackets or add metadata"
                        ),
                    )
                )
            else:
                raw = metadata_str
                stripped = raw.strip()
                leading = len(raw) - len(raw.lstrip())
                m_offset = match.start("metadata") + leading
                metadata = self.ConnectionMetaDataParser.parse(
                    line,
                    stripped,
                    line_number,
                    m_offset,
                )

        return zone1, zone2, metadata


class Connection:
    """
    Represents a unidirectional link from one hub to another.

    Manages the maximum link capacity and reservations on this link over time.
    """

    def __init__(
        self,
        hub_from: Hub,
        hub_to: Hub,
        max_link_capacity: int = 1,
    ) -> None:
        """
        Initializes a Connection.

        Args:
            hub_from (Hub): The hub from which this connection originates.
            hub_to (Hub): The destination hub of this connection.
            max_link_capacity (int): The maximum number of drones that can
                traverse this link concurrently. Defaults to 1.
        """
        self.__hub_from: str = str(hub_from)
        self.__hub_to: Hub = hub_to
        self.__max_link_capacity: int = max_link_capacity
        self.__reservations: Dict[int, int] = {}

    @property
    def hub_from(self) -> str:
        """str: The string representation of the source hub."""
        return self.__hub_from

    @property
    def hub_to(self) -> Hub:
        """Hub: The destination hub."""
        return self.__hub_to

    @property
    def max_link_capacity(self) -> int:
        """int: The maximum concurrent drone capacity of this connection."""
        return self.__max_link_capacity

    def can_reserve(self, time: int) -> bool:
        """
        Checks if the connection can be reserved at a specific time.

        Args:
            time (int): The turn number to check.

        Returns:
            bool: True if there is remaining capacity, False otherwise.
        """
        return self.__reservations.get(time, 0) < self.__max_link_capacity

    def reserve(self, time: int) -> bool:
        """
        Reserves the connection at the given time.

        Args:
            time (int): The turn number to reserve.

        Returns:
            bool: True if reservation was successful, False if it was already
                at max capacity.
        """
        if not self.can_reserve(time):
            return False
        self.__reservations[time] = self.__reservations.get(time, 0) + 1
        return True

    def nearest_reservation(
        self,
        start_time: int,
    ) -> int:
        """
        Finds the nearest future time from start_time when the connection can
        be reserved.

        Args:
            start_time (int): The time to start checking from.

        Returns:
            int: The first available time >= start_time.
        """
        time = start_time
        while not self.can_reserve(time):
            time += 1
        return time

    def __str__(self) -> str:
        """
        Returns the string representation of the connection.

        Returns:
            str: Formatting representing the link, e.g., "hub_from-hub_to".
        """
        return f"{self.__hub_from}-{self.__hub_to}"
