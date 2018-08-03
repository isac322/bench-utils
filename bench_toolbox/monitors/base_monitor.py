# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Iterable

from monitors import MonitorData
from monitors.handlers.base_handler import BaseHandler


class BaseMonitor(metaclass=ABCMeta):
    def __init__(self, interval: int, handlers: Iterable[BaseHandler[MonitorData]]) -> None:
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
        await asyncio.wait(tuple(handler.on_destroy() for handler in self._handlers))
