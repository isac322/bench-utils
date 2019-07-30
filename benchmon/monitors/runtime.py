# coding: UTF-8

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .base import BaseMonitor
from .messages import PerBenchMessage
from .pipelines import BasePipeline
from ..benchmark import BaseBenchmark

if TYPE_CHECKING:
    from .. import Context


# TODO: handle pause and resume of Benchmark
class RuntimeMonitor(BaseMonitor[PerBenchMessage, float]):
    __slots__ = ('_start_time',)

    _start_time: float

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        from benchmon.benchmark import LaunchableBenchmark
        benchmark = BaseBenchmark.of(context)
        if isinstance(benchmark, LaunchableBenchmark):
            self._start_time = benchmark.launched_time
        else:
            self._start_time = time.time()

    async def _monitor(self, context: Context) -> None:
        await BaseBenchmark.of(context).join()

        end = time.time()
        msg = await self.create_message(context, end - self._start_time)
        await BasePipeline.of(context).on_message(context, msg)

    async def stop(self) -> None:
        pass

    async def create_message(self, context: Context, data: float) -> PerBenchMessage[float]:
        return PerBenchMessage(data, self, BaseBenchmark.of(context))
