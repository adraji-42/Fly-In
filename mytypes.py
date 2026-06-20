from enum import StrEnum
from typing import Dict, Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from hub import Hub, StartHub, EndHub


class HubType(StrEnum):
    """
    Enum representing the different types of zones a hub can be.

    Attributes:
        NORMAL: Standard hub with capacity.
        BLOCKED: Hub that cannot be entered.
        RESTRICTED: Hub that has an additional time cost (2 turns).
        PRIORITY: Hub that is prioritized during pathfinding.
    """

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


HubMetaData = Union[HubType, str, int]
HubAttribute = Tuple[str, str, int, int, Dict[str, HubMetaData]]
ConnectionAttribute = Tuple[str, str, int]
MapAttributes = Tuple[int, "StartHub", Dict[str, "Hub"], "EndHub"]
