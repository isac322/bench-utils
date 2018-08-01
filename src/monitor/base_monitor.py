# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Iterable

from monitor.handlers.base_handler import BaseHandler


class BaseMonitor(metaclass=ABCMeta):
    def __init__(self, interval: int, handlers: Iterable[BaseHandler, ...]) -> None:
        self._interval: int = interval
        self._handlers = tuple(handlers)

    @abstractmethod
    async def monitor(self) -> None:
        pass

    def on_init(self) -> None:
        pass

    def on_end(self) -> None:
        pass

    def on_destroy(self) -> None:
        pass
