from enum import StrEnum
from typing import Dict, Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from hub import Hub, StartHub, EndHub


class ZoneType(StrEnum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


HubMetaData = Union[ZoneType, str, int]
HubAttribute = Tuple[str, str, int, int, Dict[str, HubMetaData]]
ConnectionAttribute = Tuple[str, str, int]
MapAttributes = Tuple[int, "StartHub", Dict[str, "Hub"], "EndHub"]
