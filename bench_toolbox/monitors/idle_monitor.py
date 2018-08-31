# coding: UTF-8

from typing import Mapping

from . import MonitorData
from .base_monitor import BaseMonitor
from .messages import BaseMessage
from ..benchmark import BaseBenchmark


class IdleMonitor(BaseMonitor):
    async def create_message(self, data: Mapping[str, MonitorData]) -> BaseMessage:
        pass

    def __init__(self, benchmark: BaseBenchmark) -> None:
        super().__init__(lambda x: None)

        self._benchmark = benchmark

    async def _monitor(self) -> None:
        await self._benchmark.join()
