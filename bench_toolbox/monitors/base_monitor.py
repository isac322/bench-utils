# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Iterable, Tuple

from . import MonitorData
from .handlers.base_handler import BaseHandler


class BaseMonitor(metaclass=ABCMeta):
    def __init__(self, handlers: Iterable[BaseHandler[MonitorData]] = tuple()) -> None:
        self._handlers: Tuple[BaseHandler[MonitorData], ...] = tuple(handlers)
        self._initialized = False

    async def monitor(self) -> None:
        if not self._initialized:
            raise AssertionError('"on_init()" must be invoked before "monitor()"')

        try:
            await self._monitor()

        except asyncio.CancelledError as e:
            await self.on_cancel(e)

    @abstractmethod
    async def _monitor(self) -> None:
        pass

    async def on_cancel(self, cancel_error: asyncio.CancelledError) -> None:
        pass

    async def on_init(self) -> None:
        if self._initialized:
            raise AssertionError('This monitor has already been initialized.')
        else:
            self._initialized = True

    async def on_end(self) -> None:
        pass

    async def on_destroy(self) -> None:
        if len(self._handlers) is not 0:
            await asyncio.wait(tuple(handler.on_destroy() for handler in self._handlers))
