# coding: UTF-8

from typing import Mapping

import rdtsc

from monitor.oneshot_monitor import OneShotMonitor


class RDTSCMonitor(OneShotMonitor[int]):
    async def monitor_once(self) -> Mapping[str, int]:
        return dict(rdtsc=rdtsc.get_cycles())
