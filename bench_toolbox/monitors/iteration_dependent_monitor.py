# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Iterable, Mapping

from . import MonitorData
from .handlers.base_handler import BaseHandler
from .oneshot_monitor import OneShotMonitor


class IterationDependentMonitor(OneShotMonitor, metaclass=ABCMeta):
    def __init__(self, handlers: Iterable[BaseHandler, ...], interval: int) -> None:
        super().__init__(handlers, interval)

        self._prev_data: Mapping[str, MonitorData] = None

    async def _monitor(self) -> None:
        while True:
            data = await self.monitor_once()
            diff = self.calc_diff(self._prev_data, data)
            self._prev_data = data

            transformed = self._transform_data(diff)

            await asyncio.wait((self._handle_data(transformed), asyncio.sleep(self._interval)))

    @abstractmethod
    def calc_diff(self, before: Mapping[str, MonitorData], after: Mapping[str, MonitorData]) \
            -> Mapping[str, MonitorData]:
        pass
