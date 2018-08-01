# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Iterable, Mapping, Tuple, TypeVar

from monitor.handlers.base_handler import BaseHandler

MonitorData = TypeVar('MonitorData', int, float, Tuple, Mapping)


class BaseMonitor(metaclass=ABCMeta):
    def __init__(self, interval: int, handlers: Iterable[BaseHandler, ...]) -> None:
        self._interval: int = interval
        self._handlers = tuple(handlers)

    @abstractmethod
    async def monitor(self) -> None:
        pass

    async def on_init(self) -> None:
        pass

    async def on_end(self) -> None:
        pass

    async def on_destroy(self) -> None:
        pass
