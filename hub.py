from typing import Dict
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
            if HubRegex.HUB_METADATA.match(metadata_str):
                metadata = dict()

                for key, value in HubRegex.PAIRS_KV.findall(metadata_str):
                    key, value = key.strip(), value.strip()

                    if key == "zone":
                        try:
                            metadata[key] = ZoneType(value)
                        except ValueError:
                            raise HubMetaDataParsingError()
                    elif key == "color":
                        if not value.isalpha():
                            raise HubMetaDataParsingError()
                        metadata[key] = value
                    elif key == "max_drones":
                        try:
                            metadata[key] = int(value)
                        except ValueError:
                            raise HubMetaDataParsingError()
                    else:
                        raise HubMetaDataParsingError()

                return metadata
            else:
                raise HubMetaDataParsingError()

    def parse(self, line: str) -> HubAttribut:
        match = HubRegex.HUB_LINE.match(line)

        if not match:
            raise HubParsingError()

        _type = match.group("type").lower()
        name = match.group("name")
        x, y = match.group("x"), match.group("y")
        name_match = HubRegex.ZONE_NAME.match(name)
        type_match = HubRegex.HUB_TYPE.match(_type)
        x_match = HubRegex.ZONE_COORDINATE.match(x)
        y_match = HubRegex.ZONE_COORDINATE.match(y)

        if not type_match:
            raise HubParsingError()
        if not name_match:
            raise HubParsingError()
        if not x_match:
            raise HubParsingError()
        if not y_match:
            raise HubParsingError()

        metadata_str = match.group("metadata")

        if metadata_str is None:
            metadata = {
                "zone": ZoneType.NORMAL,
                "color": "white",
                "max_drones": 1
            }
        elif not metadata_str.strip():
            raise HubMetaDataParsingError()
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
        self.__zone = metadata.get("zone", ZoneType.NORMAL)
        self.__color = metadata.get("color", "white")
        self.__max_drones = metadata.get("max_drones", 1)

    @property
    def zone(self) -> ZoneType:
        return self.__zone

    @property
    def color(self) -> str:
        return self.__color

    @property
    def max_drones(self) -> int:
        return self.__max_drones

    def __str__(self):
        return f"Hub(name={self.name}, x={self.x}, y={self.y}, " \
               f"zone={self.zone}, color={self.color}, " \
               f"max_drones={self.max_drones})"


class StartHub(Hub):
    ...


class EndHub(Hub):
    ...
