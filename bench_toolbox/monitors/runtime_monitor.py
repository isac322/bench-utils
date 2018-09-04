# coding: UTF-8

from __future__ import annotations

import time
from typing import Callable, Coroutine, Type

from . import MonitorData
from .base_builder import BaseBuilder
from .base_monitor import BaseMonitor
from .messages import BaseMessage
from .messages.per_bench_message import PerBenchMessage
from ..benchmark import BaseBenchmark


# TODO: handle pause and resume of Benchmark
class RuntimeMonitor(BaseMonitor[float]):
    _start_time: float
    _benchmark: BaseBenchmark

    def __new__(cls: Type[BaseMonitor],
                emitter: Callable[[BaseMessage[MonitorData]], Coroutine[None, None, None]],
                benchmark: BaseBenchmark) -> RuntimeMonitor:
        obj: RuntimeMonitor = super().__new__(cls, emitter)

        obj._benchmark = benchmark

        return obj

    async def on_init(self) -> None:
        await super().on_init()

        self._start_time = time.time()

    async def _monitor(self) -> None:
        await self._benchmark.join()

    async def on_end(self) -> None:
        end = time.time()
        msg = await self.create_message(end - self._start_time)
        await self._emitter(msg)

    async def create_message(self, data: float) -> PerBenchMessage[float]:
        return PerBenchMessage(data, self, self._benchmark)

    class Builder(BaseBuilder['RuntimeMonitor']):
        def _finalize(self) -> RuntimeMonitor:
            return RuntimeMonitor.__new__(RuntimeMonitor, self._cur_emitter, self._cur_bench)
