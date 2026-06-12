from __future__ import annotations

from hub import Hub
from path import Path
from typing import Iterator, Optional


class Drone:

    def __init__(self, id: int, hub: Hub) -> None:
        self._id: int = id
        self.__current_hub: Hub = hub
        self.__path: Optional[Path] = None
        self.__path_iter: Optional[Iterator[Hub]] = None
        self.__next_hub: Optional[Hub] = None

    @property
    def path(self) -> Optional[Path]:
        return self.__path

    @path.setter
    def path(self, path: Path) -> None:
        self.__path = path
        hubs = path.hubs
        try:
            start_index = next(
                i for i, h in enumerate(hubs)
                if h is self.__current_hub
            )
        except StopIteration:
            start_index = 0
        self.__path_iter = iter(hubs[start_index + 1:])
        self.__next_hub = next(self.__path_iter, None)

    @property
    def current_hub(self) -> Hub:
        return self.__current_hub

    @property
    def in_transit(self) -> bool:
        return self.__next_hub is not None

    @property
    def finished(self) -> bool:
        if self.__path is None:
            return False
        last = self.__path.hubs[-1]
        return self.__current_hub is last

    def step(self) -> Optional[str]:
        if self.__next_hub is None:
            return None

        dest = self.__next_hub

        if not dest.can_land:
            return None

        self.__current_hub.leaving()
        dest.land()
        self.__current_hub = dest

        self.__next_hub = next(self.__path_iter, None)

        return f"D{self._id}-{dest.name}"

    def __repr__(self) -> str:
        return (
            f"Drone(id={self._id}, "
            f"hub={self.__current_hub.name}, "
            f"finished={self.finished})"
        )
