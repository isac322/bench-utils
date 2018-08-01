# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Iterable, Mapping

from monitor.handlers.base_handler import BaseHandler
from monitor.oneshot_monitor import OneShotMonitor
from monitor.base_monitor import MonitorData


class IterationDependentMonitor(OneShotMonitor, metaclass=ABCMeta):
    def __init__(self, interval: int, handlers: Iterable[BaseHandler, ...]) -> None:
        super().__init__(interval, handlers)
        self._prev_data: Mapping[str, MonitorData] = None

    async def monitor(self) -> None:
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
