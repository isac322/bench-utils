# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import Callable, Coroutine, Type

from . import MonitorData
from .base import BaseMonitor
from .messages import BaseMessage


# FIXME: rename
class OneShotMonitor(BaseMonitor[MonitorData], metaclass=ABCMeta):
    _interval: float

    def __new__(cls: Type[OneShotMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]],
                interval: int) -> OneShotMonitor:
        obj: OneShotMonitor = super().__new__(cls, emitter)

        obj._interval = interval / 1000

        return obj

    async def _monitor(self) -> None:
        while not self.stopped:
            data = await self.monitor_once()
            transformed = self._transform_data(data)

            message = await self.create_message(transformed)
            await self._emitter(message)

            await asyncio.sleep(self._interval)

    @abstractmethod
    async def monitor_once(self) -> MonitorData:
        pass

    @property
    @abstractmethod
    def stopped(self) -> bool:
        pass

    # noinspection PyMethodMayBeStatic
    def _transform_data(self, data: MonitorData) -> MonitorData:
        return data
