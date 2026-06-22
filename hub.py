from pygame import Color
from myregex import HubRegex
from zone import Zone, ZoneParser
from typing import Dict, cast, Optional
from mytypes import HubType, HubAttribute, HubMetaData
from exceptions import (
    MapFormatError,
    ErrorInfo,
    HubLineInspector,
    HubMetadataInspector,
)


class HubParser(ZoneParser):
    """
    Parser for hub definitions in the map file.

    Extracts hub attributes including type, name, coordinates, and metadata.
    """

    class HubMetaDataParser:
        """
        Sub-parser for handling the metadata block within a hub definition
        line.
        """

        @staticmethod
        def parse(
            line: str,
            metadata_str: str,
            line_number: int,
            metadata_offset: int,
        ) -> Dict[str, HubMetaData]:
            """
            Parses the metadata string into a dictionary of HubMetaData.

            Args:
                line (str): The original line from the map file.
                metadata_str (str): The extracted metadata string (content
                    inside brackets).
                line_number (int): The current line number in the file.
                metadata_offset (int): The character offset where metadata
                    begins in the line.

            Returns:
                Dict[str, HubMetaData]: The parsed metadata key-value pairs.

            Raises:
                MapFormatError: If the metadata format is invalid or contains
                    unexpected keys/values.
            """
            if not HubRegex.HUB_METADATA.match(metadata_str):
                raise MapFormatError(
                    HubMetadataInspector.inspect(
                        line,
                        metadata_str,
                        line_number,
                        metadata_offset,
                    )
                )

            metadata: Dict[str, HubMetaData] = dict()
            remaining = metadata_str.strip()
            search_from = metadata_offset

            while remaining:
                match = HubRegex.PAIRS_KV.match(remaining)
                if not match:
                    raise MapFormatError(
                        HubMetadataInspector.inspect(
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

                if key == "zone":
                    try:
                        metadata[key] = HubType(value.lower())
                    except ValueError:
                        raise MapFormatError(
                            ErrorInfo(
                                line_number=line_number,
                                line_content=line,
                                error_start=val_pos,
                                error_end=val_pos + len(value),
                                reason=(
                                    f"'{value}' is not a" " valid zone type"
                                ),
                                expected=(
                                    "normal, blocked,"
                                    " restricted, or priority"
                                ),
                                how_to_fix=(
                                    f"replace '{value}' with"
                                    " a valid zone type"
                                ),
                            )
                        )
                elif key == "color":
                    if not value.isalpha():
                        raise MapFormatError(
                            ErrorInfo(
                                line_number=line_number,
                                line_content=line,
                                error_start=val_pos,
                                error_end=val_pos + len(value),
                                reason=(
                                    f"'{value}' is not a" " valid color name"
                                ),
                                expected=(
                                    "letters only, such as" " blue or red"
                                ),
                                how_to_fix=(
                                    "remove digits or"
                                    " punctuation from"
                                    " the color value"
                                ),
                            )
                        )
                    metadata[key] = value.lower()
                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                        if max_drones <= 0:
                            raise MapFormatError(
                                ErrorInfo(
                                    line_number=line_number,
                                    line_content=line,
                                    error_start=val_pos,
                                    error_end=(val_pos + len(value)),
                                    reason=(
                                        f"'{value}' must be" " greater than 0"
                                    ),
                                    expected=(
                                        "a positive integer" " greater than 0"
                                    ),
                                    how_to_fix=(
                                        "use a positive number"
                                        " for max_drones"
                                    ),
                                )
                            )
                        metadata[key] = max_drones
                    except ValueError:
                        raise MapFormatError(
                            ErrorInfo(
                                line_number=line_number,
                                line_content=line,
                                error_start=val_pos,
                                error_end=val_pos + len(value),
                                reason=(
                                    f"'{value}' is not a" " valid integer"
                                ),
                                expected=("an integer, such as" " 1 or 5"),
                                how_to_fix=(
                                    "replace max_drones value"
                                    " with a whole number"
                                ),
                            )
                        )
                else:
                    raise MapFormatError(
                        ErrorInfo(
                            line_number=line_number,
                            line_content=line,
                            error_start=key_pos,
                            error_end=key_pos + len(key),
                            reason=(
                                f"'{key}' is not a valid" " hub metadata key"
                            ),
                            expected=("zone, color, or max_drones"),
                            how_to_fix=(
                                "rename the key to a"
                                " supported metadata key"
                                " or remove it"
                            ),
                        )
                    )

            return metadata

    def parse(
        self,
        line: str,
        line_number: int,
    ) -> HubAttribute:
        """
        Parses a full hub definition line.

        Args:
            line (str): The raw line string from the map file.
            line_number (int): The line number in the map file.

        Returns:
            HubAttribute: A tuple containing the hub type, name, x, y
                coordinates, and metadata.

        Raises:
            MapFormatError: If the line format is invalid or missing required
                components.
        """
        match = HubRegex.HUB_LINE.match(line)

        if not match:
            raise MapFormatError(HubLineInspector.inspect(line, line_number))

        _type = match.group("type").lower()
        name = match.group("name")
        x, y = match.group("x"), match.group("y")
        name_match = HubRegex.ZONE_NAME.match(name)
        type_match = HubRegex.HUB_TYPE.match(_type)
        x_match = HubRegex.ZONE_COORDINATE.match(x)
        y_match = HubRegex.ZONE_COORDINATE.match(y)

        if not type_match:
            raise MapFormatError(
                ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=match.start("type"),
                    error_end=match.end("type"),
                    reason=(f"'{_type}' is not a valid hub type"),
                    expected=("start_hub, hub, or end_hub"),
                    how_to_fix=(
                        "use start_hub, hub," " or end_hub as the type"
                    ),
                )
            )
        if not name_match:
            raise MapFormatError(
                ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=match.start("name"),
                    error_end=match.end("name"),
                    reason=(f"'{name}' is not a valid hub name"),
                    expected=("a name without dashes or spaces"),
                    how_to_fix=(f"rename '{name}' to a" " valid identifier"),
                )
            )
        if not x_match:
            raise MapFormatError(
                ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=match.start("x"),
                    error_end=match.end("x"),
                    reason=(f"'{x}' is not a valid x coordinate"),
                    expected="an integer value for x",
                    how_to_fix=(f"replace '{x}' with a valid integer"),
                )
            )
        if not y_match:
            raise MapFormatError(
                ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=match.start("y"),
                    error_end=match.end("y"),
                    reason=(f"'{y}' is not a valid y coordinate"),
                    expected="an integer value for y",
                    how_to_fix=(f"replace '{y}' with a valid integer"),
                )
            )

        metadata_str = match.group("metadata")

        metadata: Dict[str, HubMetaData]
        if metadata_str is None:
            metadata = {
                "zone": HubType.NORMAL,
                "color": "none",
                "max_drones": 1,
            }
        elif not metadata_str.strip():
            bracket_start = line.find("[")
            bracket_end = line.find("]", bracket_start) + 1
            raise MapFormatError(
                ErrorInfo(
                    line_number=line_number,
                    line_content=line,
                    error_start=bracket_start,
                    error_end=bracket_end,
                    reason="the metadata block is empty",
                    expected=("key=value pairs" " or no brackets at all"),
                    how_to_fix=(
                        "remove the empty brackets" " or add metadata"
                    ),
                )
            )
        else:
            raw = metadata_str
            stripped = raw.strip()
            leading = len(raw) - len(raw.lstrip())
            m_offset = match.start("metadata") + leading
            metadata = self.HubMetaDataParser.parse(
                line,
                stripped,
                line_number,
                m_offset,
            )

        return _type, name, int(x), int(y), metadata


class Hub(Zone):
    """
    Represents a Hub zone on the map.

    Inherits from Zone. Supports properties such as hub type, display color,
    maximum
    drones capacity, traversal cost, and manages reservations.
    """

    COST_MAP: Dict[HubType, Optional[int]] = {
        HubType.BLOCKED: None,
        HubType.RESTRICTED: 2,
    }

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        metadata: Dict[str, HubMetaData],
    ) -> None:
        """
        Initializes a Hub.

        Args:
            name (str): The name of the hub.
            x (int): The x coordinate.
            y (int): The y coordinate.
            metadata (Dict[str, HubMetaData]): Configuration metadata for the
                hub.
        """
        super().__init__(name, x, y)
        self.__type = cast(
            HubType,
            metadata.get("zone", HubType.NORMAL),
        )
        try:
            self.__color: Color = Color(metadata.get("color", "none"))
        except ValueError:
            self.__color = Color("white")
        self.__max_drones = cast(int, metadata.get("max_drones", 1))
        self.__cost: Optional[int] = self.COST_MAP.get(self.__type, 1)
        self.__reservations: Dict[int, int] = {}

    @property
    def type(self) -> HubType:
        """HubType: The type classification of the hub."""
        return self.__type

    @property
    def color(self) -> Color:
        """Color: The display color for the hub output."""
        return self.__color

    @property
    def max_drones(self) -> int:
        """int: The maximum number of drones that can occupy the hub
        concurrently."""
        return self.__max_drones

    @property
    def cost(self) -> Optional[int]:
        """Optional[int]: The cost/time to traverse this hub. None if
        blocked."""
        return self.__cost

    def can_reserve(self, time: int) -> bool:
        """
        Checks if the hub can be reserved at a specific time.

        Args:
            time (int): The turn number to check.

        Returns:
            bool: True if it can be reserved, False otherwise (e.g., if blocked
                or at capacity).
        """
        return (
            self.__type is not HubType.BLOCKED
            and self.__reservations.get(time, 0) < self.__max_drones
        )

    def reserve(self, time: int) -> None:
        """
        Reserves the hub at the given time.

        Args:
            time (int): The turn number to reserve.
        """
        self.__reservations[time] = self.__reservations.get(time, 0) + 1

    def nearest_reservation(
        self,
        start_time: int,
    ) -> int:
        """
        Finds the nearest future time from start_time when the hub can be
        reserved.

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
        Returns the string representation of the hub with ANSI color codes.

        Returns:
            str: The colored string representation.
        """
        r, g, b, _ = self.__color
        return f"\x1b[38;2;{r};{g};{b}m" f"{self.name}\x1b[0m"


class StartHub(Hub):
    """
    Represents the designated Start Hub.

    Guarantees sufficient capacity for all initial drones.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        nb_drones: int,
        metadata: Dict[str, HubMetaData],
    ) -> None:
        """
        Initializes the StartHub.

        Args:
            name (str): The name of the hub.
            x (int): The x coordinate.
            y (int): The y coordinate.
            nb_drones (int): The total number of drones that start here.
            metadata (Dict[str, HubMetaData]): Configuration metadata for the
                hub.
        """
        metadata["max_drones"] = max(
            metadata.get("max_drones", nb_drones),
            nb_drones,
        )
        super().__init__(name, x, y, metadata)


class EndHub(Hub):
    """
    Represents the designated End Hub.

    Guarantees sufficient capacity for all incoming drones.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        nb_drones: int,
        metadata: Dict[str, HubMetaData],
    ) -> None:
        """
        Initializes the EndHub.

        Args:
            name (str): The name of the hub.
            x (int): The x coordinate.
            y (int): The y coordinate.
            nb_drones (int): The total number of drones that will end here.
            metadata (Dict[str, HubMetaData]): Configuration metadata for the
                hub.
        """
        metadata["max_drones"] = max(
            metadata.get("max_drones", nb_drones),
            nb_drones,
        )
        super().__init__(name, x, y, metadata)
