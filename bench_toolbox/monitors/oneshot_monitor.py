# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Generic, Iterable, Mapping

from . import MonitorData
from .base_monitor import BaseMonitor
from .handlers.base_handler import BaseHandler


class OneShotMonitor(BaseMonitor, Generic[MonitorData], metaclass=ABCMeta):
    def __init__(self, handlers: Iterable[BaseHandler[MonitorData]], interval: int) -> None:
        super().__init__(handlers)

        self._interval: int = interval

    async def _monitor(self) -> None:
        while True:
            data = await self.monitor_once()
            transformed = self._transform_data(data)

            await asyncio.wait((*self._handle_data(transformed), asyncio.sleep(self._interval)))

    def _handle_data(self, data: Mapping[str, MonitorData]):
        return (h.handle(data) for h in self._handlers)

    @abstractmethod
    async def monitor_once(self) -> Mapping[str, MonitorData]:
        pass

    # noinspection PyMethodMayBeStatic
    def _transform_data(self, data: Mapping[str, MonitorData]) -> Mapping[str, MonitorData]:
        return data
