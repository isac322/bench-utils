# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Generic, Mapping, TYPE_CHECKING, Tuple, Type, TypeVar

if TYPE_CHECKING:
    from .. import Context
    # because of circular import
    from .messages.base import BaseMessage

MonitorData = TypeVar('MonitorData', int, float, Tuple, Mapping)


# parametrize message type too
class BaseMonitor(Generic[MonitorData], metaclass=ABCMeta):
    _initialized: bool

    def __new__(cls: Type[BaseMonitor]) -> BaseMonitor[MonitorData]:
        obj = super().__new__(cls)

        obj._initialized = False

        return obj

    async def monitor(self, context: Context) -> None:
        if not self._initialized:
            raise AssertionError('"on_init()" must be invoked before "monitor()"')

        try:
            await self._monitor(context)

        except asyncio.CancelledError as e:
            await self.on_cancel(context, e)

    @abstractmethod
    async def _monitor(self, context: Context) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def create_message(self, data: MonitorData) -> BaseMessage[MonitorData]:
        pass

    async def on_cancel(self, context: Context, cancel_error: asyncio.CancelledError) -> None:
        pass

    async def on_init(self, context: Context) -> None:
        if self._initialized:
            raise AssertionError('This monitor has already been initialized.')
        else:
            self._initialized = True

    async def on_end(self, context: Context) -> None:
        pass

    async def on_destroy(self, context: Context) -> None:
        pass
