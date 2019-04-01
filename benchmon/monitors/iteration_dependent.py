# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Optional, TYPE_CHECKING

from .base import MonitorData
from .oneshot import OneShotMonitor
from .pipelines.base import BasePipeline

if TYPE_CHECKING:
    from .. import Context


# FIXME: rename
class IterationDependentMonitor(OneShotMonitor[MonitorData]):
    _prev_data: Optional[MonitorData]

    def __init__(self, interval: int) -> None:
        super().__init__(interval)

        self._prev_data = None

    async def _monitor(self, context: Context) -> None:
        while not self.stopped:
            data = await self.monitor_once(context)
            diff = self.calc_diff(self._prev_data, data)
            self._prev_data = data

            transformed = self._transform_data(diff)

            message = await self.create_message(context, transformed)
            await BasePipeline.of(context).on_message(context, message)

            await asyncio.sleep(self._interval)

    # FIXME: rename
    @abstractmethod
    def calc_diff(self, before: MonitorData, after: MonitorData) -> MonitorData:
        pass
