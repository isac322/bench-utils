# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Generic, Optional, TYPE_CHECKING, Type, TypeVar

from .messages import BaseMessage
from .. import ContextReadable
from ..benchmark import BaseBenchmark
from ..exceptions import AlreadyInitedError, InitRequiredError

if TYPE_CHECKING:
    from .. import Context

_MT = TypeVar('_MT', bound='BaseMonitor')
_DAT_T = TypeVar('_DAT_T')
_MSG_T = TypeVar('_MSG_T', bound=BaseMessage)


# parametrize message type too
class BaseMonitor(ContextReadable, Generic[_MSG_T, _DAT_T], metaclass=ABCMeta):
    __slots__ = ('_initialized',)

    _initialized: bool

    @classmethod
    def of(cls: Type[_MT], context: Context) -> Optional[_MT]:
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
            raise InitRequiredError('"on_init()" must be invoked before "monitor()"')

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
    async def create_message(self, context: Context, data: _DAT_T) -> _MSG_T[_DAT_T]:
        pass

    # TODO: should be abstractmethod?
    async def on_cancel(self, context: Context, cancel_error: asyncio.CancelledError) -> None:
        pass

    async def on_init(self, context: Context) -> None:
        if self._initialized:
            raise AlreadyInitedError('This monitor has already been initialized.')
        else:
            self._initialized = True

    async def on_end(self, context: Context) -> None:
        pass

    async def on_destroy(self, context: Context) -> None:
        pass
