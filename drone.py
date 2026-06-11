from hub import Hub
from path import Path
from typing import Optional


class Drone:

    def __init__(self, id: int, hub: Hub) -> None:
        self._id = id
        self.__current_hub: Hub = hub
        self.__transit_destination: Optional[Hub] = None
        self.__path: Optional[Path] = None

    @property
    def path(self) -> Optional[Path]:
        return self.__path
    
    @path.setter
    def path(self, path: Path) -> None:
        self.__path = path

    @property
    def current_hub(self) -> Hub:
        return self.__current_hub

    @property
    def in_transit(self) -> bool:
        return self.__transit_destination is not None
