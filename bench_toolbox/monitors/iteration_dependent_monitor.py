# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Callable, Mapping

from . import MonitorData
from .messages import BaseMessage
from .oneshot_monitor import OneShotMonitor


class IterationDependentMonitor(OneShotMonitor, metaclass=ABCMeta):
    def __init__(self, emitter: Callable[[BaseMessage], None], interval: int) -> None:
        super().__init__(emitter, interval)

        self._prev_data: Mapping[str, MonitorData] = None

    async def _monitor(self) -> None:
        while True:
            data = await self.monitor_once()
            diff = self.calc_diff(self._prev_data, data)
            self._prev_data = data

            transformed = self._transform_data(diff)

            message = await self.create_message(transformed)
            self._emitter(message)
            await asyncio.sleep(self._interval)

    @abstractmethod
    def calc_diff(self, before: Mapping[str, MonitorData], after: Mapping[str, MonitorData]) \
            -> Mapping[str, MonitorData]:
        pass
