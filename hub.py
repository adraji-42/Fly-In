from typing import Dict, cast
from regex import HubRegex
from zone import Zone, ZoneParser
from mytyping import ZoneType, HubAttribut, HubMetaData
from exceptions import (
    HubParsingError, HubMetaDataParsingError
)


class HubParser(ZoneParser):

    class HubMetaDataParser:

        @staticmethod
        def parse(
            line: str, metadata_str: str
        ) -> Dict[str, HubMetaData]:
            if not HubRegex.HUB_METADATA.match(metadata_str):
                raise HubMetaDataParsingError(
                    line=line,
                    metadata=metadata_str,
                )

            metadata: Dict[str, HubMetaData] = dict()
            remaining = metadata_str.strip()

            while remaining:
                match = HubRegex.PAIRS_KV.match(remaining)
                if not match:
                    raise HubMetaDataParsingError(
                        line=line,
                        metadata=metadata_str,
                    )

                key = match.group("key").strip()
                value = match.group("value").strip()
                remaining = remaining[match.end():].strip()

                if key == "zone":
                    try:
                        metadata[key] = ZoneType(value)
                    except ValueError:
                        raise HubMetaDataParsingError(
                            line=line,
                            metadata=metadata_str,
                        )
                elif key == "color":
                    if not value.isalpha():
                        raise HubMetaDataParsingError(
                            line=line,
                            metadata=metadata_str,
                        )
                    metadata[key] = value
                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                        if max_drones <= 0:
                            raise HubMetaDataParsingError(
                                line=line,
                                metadata=metadata_str,
                            )
                        metadata[key] = max_drones
                    except ValueError:
                        raise HubMetaDataParsingError(
                            line=line,
                            metadata=metadata_str,
                        )
                else:
                    raise HubMetaDataParsingError(
                        line=line,
                        metadata=metadata_str,
                    )

            return metadata

    def parse(self, line: str) -> HubAttribut:
        match = HubRegex.HUB_LINE.match(line)

        if not match:
            raise HubParsingError(line=line)

        _type = match.group("type").lower()
        name = match.group("name")
        x, y = match.group("x"), match.group("y")
        name_match = HubRegex.ZONE_NAME.match(name)
        type_match = HubRegex.HUB_TYPE.match(_type)
        x_match = HubRegex.ZONE_COORDINATE.match(x)
        y_match = HubRegex.ZONE_COORDINATE.match(y)

        if not type_match:
            raise HubParsingError(line=line)
        if not name_match:
            raise HubParsingError(line=line)
        if not x_match:
            raise HubParsingError(line=line)
        if not y_match:
            raise HubParsingError(line=line)

        metadata_str = match.group("metadata")

        metadata: Dict[str, HubMetaData]
        if metadata_str is None:
            metadata = {
                "zone": ZoneType.NORMAL,
                "color": "none",
                "max_drones": 1
            }
        elif not metadata_str.strip():
            raise HubMetaDataParsingError(line=line, metadata=metadata_str)
        else:
            metadata = self.HubMetaDataParser.parse(
                line, metadata_str.strip()
            )

        return _type, name, int(x), int(y), metadata


class Hub(Zone):
    def __init__(
        self, name: str, x: int, y: int, metadata: Dict[str, HubMetaData]
    ) -> None:
        super().__init__(name, x, y)
        self.__type = cast(ZoneType, metadata.get("zone", ZoneType.NORMAL))
        self.__color = cast(str, metadata.get("color", "none"))
        self.__max_drones = cast(int, metadata.get("max_drones", 1))

    @property
    def type(self) -> ZoneType:
        return self.__type

    @property
    def color(self) -> str:
        return self.__color

    @property
    def max_drones(self) -> int:
        return self.__max_drones


class StartHub(Hub):
    def __init__(
        self, name: str, x: int, y: int,
        nb_drones: int, metadata: Dict[str, HubMetaData]
    ) -> None:
        metadata["max_drones"] = max(
            metadata.get("max_drones", nb_drones), nb_drones
        )
        super().__init__(name, x, y, metadata)
        self._nb_drones_currently = nb_drones


class EndHub(Hub):
    def __init__(
        self, name: str, x: int, y: int,
        nb_drones: int, metadata: Dict[str, HubMetaData]
    ) -> None:
        metadata["max_drones"] = max(
            metadata.get("max_drones", nb_drones), nb_drones
        )
        super().__init__(name, x, y, metadata)
