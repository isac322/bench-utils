# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Callable, Coroutine, Optional, Type

from . import MonitorData
from .messages import BaseMessage
from .oneshot import OneShotMonitor


# FIXME: rename
class IterationDependentMonitor(OneShotMonitor[MonitorData], metaclass=ABCMeta):
    _prev_data: Optional[MonitorData]

    def __new__(cls: Type[IterationDependentMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]],
                interval: int) -> IterationDependentMonitor:
        obj: IterationDependentMonitor = super().__new__(cls, emitter, interval)

        obj._prev_data = None

        return obj

    async def _monitor(self) -> None:
        while not self.stopped:
            data = await self.monitor_once()
            diff = self.calc_diff(self._prev_data, data)
            self._prev_data = data

            transformed = self._transform_data(diff)

            message = await self.create_message(transformed)
            await self._emitter(message)

            await asyncio.sleep(self._interval)

    # FIXME: rename
    @abstractmethod
    def calc_diff(self, before: MonitorData, after: MonitorData) -> MonitorData:
        pass
