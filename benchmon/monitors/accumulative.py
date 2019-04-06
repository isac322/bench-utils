# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Generic, Optional, TYPE_CHECKING, TypeVar

from .interval import IntervalMonitor
from .messages import BaseMessage
from .pipelines.base import BasePipeline

if TYPE_CHECKING:
    from .. import Context

_DAT_T = TypeVar('_DAT_T')
_MSG_T = TypeVar('_MSG_T', bound=BaseMessage)


class AccumulativeMonitor(IntervalMonitor[_MSG_T, _DAT_T], Generic[_MSG_T, _DAT_T]):
    _prev_data: Optional[_DAT_T]

    def __init__(self, interval: int) -> None:
        super().__init__(interval)

        self._prev_data = None

    async def _monitor(self, context: Context) -> None:
        while not self.stopped:
            data = await self.monitor_once(context)
            diff = self.accumulate(self._prev_data, data)
            self._prev_data = data

            transformed = self._transform_data(diff)

            message = await self.create_message(context, transformed)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    @abstractmethod
    def accumulate(self, before: _DAT_T, after: _DAT_T) -> _DAT_T:
        pass
