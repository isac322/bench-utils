# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Coroutine, Type

from . import MonitorData
from .base_monitor import BaseMonitor
from .messages import BaseMessage


class OneShotMonitor(BaseMonitor[MonitorData], metaclass=ABCMeta):
    _interval: float

    def __new__(cls: Type[OneShotMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]],
                interval: int) -> Any:
        obj = super().__new__(cls, emitter)

        obj._interval = interval / 1000

        return obj

    async def _monitor(self) -> None:
        while True:
            data = await self.monitor_once()
            transformed = self._transform_data(data)

            message = await self.create_message(transformed)
            await self._emitter(message)

            await asyncio.sleep(self._interval)

    @abstractmethod
    async def monitor_once(self) -> MonitorData:
        pass

    # noinspection PyMethodMayBeStatic
    def _transform_data(self, data: MonitorData) -> MonitorData:
        return data
