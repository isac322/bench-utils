# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Type

from .base import BaseMonitor, MonitorData
from .pipelines.base import BasePipeline

if TYPE_CHECKING:
    from .. import Context


# FIXME: rename
class OneShotMonitor(BaseMonitor[MonitorData], metaclass=ABCMeta):
    _interval: float

    def __new__(cls: Type[OneShotMonitor], interval: int) -> OneShotMonitor:
        obj: OneShotMonitor = super().__new__(cls)

        obj._interval = interval / 1000

        return obj

    async def _monitor(self, context: Context) -> None:
        while not self.stopped:
            data = await self.monitor_once(context)
            transformed = self._transform_data(data)

            message = await self.create_message(transformed)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    @abstractmethod
    async def monitor_once(self, context: Context) -> MonitorData:
        pass

    @property
    @abstractmethod
    def stopped(self) -> bool:
        pass

    # noinspection PyMethodMayBeStatic
    def _transform_data(self, data: MonitorData) -> MonitorData:
        return data
