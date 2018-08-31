# coding: UTF-8

from typing import Mapping

import rdtsc

from . import MonitorData
from .messages import BaseMessage
from .oneshot_monitor import OneShotMonitor


class RDTSCMonitor(OneShotMonitor[int]):
    async def create_message(self, data: Mapping[str, MonitorData]) -> BaseMessage:
        # TODO
        pass

    async def monitor_once(self) -> Mapping[str, int]:
        return dict(rdtsc=rdtsc.get_cycles())
