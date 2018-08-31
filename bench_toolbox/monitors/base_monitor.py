# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Callable, Generic, Mapping

from . import MonitorData
from .messages import BaseMessage


# parametrize message type too
class BaseMonitor(Generic[MonitorData], metaclass=ABCMeta):
    def __init__(self, emitter: Callable[[BaseMessage], None]) -> None:
        self._initialized = False
        self._emitter = emitter

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

    @abstractmethod
    async def create_message(self, data: Mapping[str, MonitorData]) -> BaseMessage:
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
        pass
