# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Iterable

from . import MonitorData
from .handlers.base_handler import BaseHandler


class BaseMonitor(metaclass=ABCMeta):
    def __init__(self, handlers: Iterable[BaseHandler[MonitorData]]) -> None:
        self._handlers = tuple(handlers)

    async def monitor(self) -> None:
        try:
            await self._monitor()

        except asyncio.CancelledError as e:
            await self.on_cancel(e)
            raise

    @abstractmethod
    async def _monitor(self) -> None:
        pass

    async def on_cancel(self, cancel_error: asyncio.CancelledError) -> None:
        pass

    async def on_init(self) -> None:
        pass

    async def on_end(self) -> None:
        pass

    async def on_destroy(self) -> None:
        if len(self._handlers) is not 0:
            await asyncio.wait(tuple(handler.on_destroy() for handler in self._handlers))
