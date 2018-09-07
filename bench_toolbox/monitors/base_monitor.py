# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Callable, Coroutine, Generic, Type

from . import MonitorData
from .messages import BaseMessage


# parametrize message type too
class BaseMonitor(Generic[MonitorData], metaclass=ABCMeta):
    _initialized: bool
    _emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]]

    def __new__(cls: Type[BaseMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]]) -> BaseMonitor:
        obj = super().__new__(cls)

        obj._initialized = False
        obj._emitter = emitter

        return obj

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
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def create_message(self, data: MonitorData) -> BaseMessage[MonitorData]:
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
