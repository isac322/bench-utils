# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Generic, Mapping, Optional, TYPE_CHECKING, Tuple, Type, TypeVar

from .. import ContextReadable
from ..benchmark import BaseBenchmark

if TYPE_CHECKING:
    from .messages import BaseMessage
    from .. import Context

MonitorData = TypeVar('MonitorData', int, float, Tuple, Mapping)

_CT = TypeVar('_CT', bound='BaseMonitor')


# parametrize message type too
class BaseMonitor(ContextReadable, Generic[MonitorData], metaclass=ABCMeta):
    _initialized: bool

    @classmethod
    def of(cls: Type[_CT], context: Context) -> Optional[_CT]:
        benchmark = BaseBenchmark.of(context)

        # noinspection PyProtectedMember
        for monitor in benchmark._monitors:
            if isinstance(monitor, cls):
                return monitor

        return None

    def __init__(self) -> None:
        self._initialized = False

    async def monitor(self, context: Context) -> None:
        if not self._initialized:
            # FIXME: detail exception type
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
    async def create_message(self, context: Context, data: MonitorData) -> BaseMessage[MonitorData]:
        pass

    # TODO: should be abstractmethod?
    async def on_cancel(self, context: Context, cancel_error: asyncio.CancelledError) -> None:
        pass

    async def on_init(self, context: Context) -> None:
        if self._initialized:
            # FIXME: detail exception type
            raise AssertionError('This monitor has already been initialized.')
        else:
            self._initialized = True

    async def on_end(self, context: Context) -> None:
        pass

    async def on_destroy(self, context: Context) -> None:
        pass
