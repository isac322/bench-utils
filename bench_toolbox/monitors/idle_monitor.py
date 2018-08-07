# coding: UTF-8

from .base_monitor import BaseMonitor
from ..benchmark.drivers import BenchDriver


class IdleMonitor(BaseMonitor):
    def __init__(self, bench_driver: BenchDriver) -> None:
        super().__init__(tuple())

        self._bench_driver: BenchDriver = bench_driver

    async def _monitor(self) -> None:
        await self._bench_driver.join()
