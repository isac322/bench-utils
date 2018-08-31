# coding: UTF-8

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Callable, Generic, Mapping

from . import MonitorData
from .base_monitor import BaseMonitor
from .messages import BaseMessage


class OneShotMonitor(BaseMonitor, Generic[MonitorData], metaclass=ABCMeta):
    def __init__(self, emitter: Callable[[BaseMessage], None], interval: int) -> None:
        super().__init__(emitter)

        self._interval: int = interval

    async def _monitor(self) -> None:
        while True:
            data = await self.monitor_once()
            transformed = self._transform_data(data)

            message = await self.create_message(transformed)
            self._emitter(message)
            await asyncio.sleep(self._interval)

    @abstractmethod
    async def create_message(self, data: Mapping[str, MonitorData]) -> BaseMessage:
        pass

    @abstractmethod
    async def monitor_once(self) -> Mapping[str, MonitorData]:
        pass

    # noinspection PyMethodMayBeStatic
    def _transform_data(self, data: Mapping[str, MonitorData]) -> Mapping[str, MonitorData]:
        return data
