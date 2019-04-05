# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Generic, TYPE_CHECKING, TypeVar

from .base import BaseMonitor
from .messages import BaseMessage
from .pipelines import BasePipeline

if TYPE_CHECKING:
    from .. import Context

_DAT_T = TypeVar('_DAT_T')
_MSG_T = TypeVar('_MSG_T', bound=BaseMessage)


# FIXME: rename
class OneShotMonitor(BaseMonitor[_MSG_T, _DAT_T], Generic[_MSG_T, _DAT_T]):
    _interval: float

    def __init__(self, interval: int) -> None:
        super().__init__()

        self._interval = interval / 1000

    async def _monitor(self, context: Context) -> None:
        while not self.stopped:
            data = await self.monitor_once(context)
            transformed = self._transform_data(data)

            message = await self.create_message(context, transformed)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    @abstractmethod
    async def monitor_once(self, context: Context) -> _DAT_T:
        pass

    @property
    @abstractmethod
    def stopped(self) -> bool:
        pass

    # noinspection PyMethodMayBeStatic
    def _transform_data(self, data: _DAT_T) -> _DAT_T:
        return data
