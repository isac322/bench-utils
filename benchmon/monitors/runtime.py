# coding: UTF-8

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Type

from .base import BaseMonitor
from .base_builder import BaseBuilder
from .messages import PerBenchMessage
from .pipelines.base import BasePipeline

if TYPE_CHECKING:
    from .. import Context
    # because of circular import
    from ..benchmark import BaseBenchmark


# TODO: handle pause and resume of Benchmark
class RuntimeMonitor(BaseMonitor[float]):
    _start_time: float
    _benchmark: BaseBenchmark

    def __new__(cls: Type[BaseMonitor], benchmark: BaseBenchmark) -> RuntimeMonitor:
        obj: RuntimeMonitor = super().__new__(cls)

        obj._benchmark = benchmark

        return obj

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        self._start_time = time.time()

    async def _monitor(self, context: Context) -> None:
        await self._benchmark.join()

        end = time.time()
        msg = await self.create_message(end - self._start_time)
        await BasePipeline.of(context).on_message(context, msg)

    async def stop(self) -> None:
        pass

    async def create_message(self, data: float) -> PerBenchMessage[float]:
        return PerBenchMessage(data, self, self._benchmark)

    class Builder(BaseBuilder['RuntimeMonitor']):
        def _finalize(self) -> RuntimeMonitor:
            return RuntimeMonitor.__new__(RuntimeMonitor, self._cur_bench)
