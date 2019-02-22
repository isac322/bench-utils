# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Mapping, TYPE_CHECKING, Union

from .base import BaseMonitor
from .messages import PerBenchMessage
from .pipelines.base import BasePipeline
from ..benchmark import BaseBenchmark

if TYPE_CHECKING:
    from .. import Context
    from ..configs.containers import PerfConfig

T = Mapping[str, Union[int, float]]


class PerfMonitor(BaseMonitor[T]):
    _perf_config: PerfConfig
    _is_stopped: bool = False

    def __init__(self, perf_config: PerfConfig) -> None:
        super().__init__()

        self._perf_config = perf_config

    async def _monitor(self, context: Context) -> None:
        benchmark = BaseBenchmark.of(context)

        perf_proc = await asyncio.create_subprocess_exec(
                'perf', 'stat', '-e', self._perf_config.event_str,
                '-p', str(benchmark.pid), '-x', ',', '-I', str(self._perf_config.interval),
                stderr=asyncio.subprocess.PIPE)

        if self._perf_config.interval < 100:
            proc = await asyncio.create_subprocess_exec('perf', '--version',
                                                        stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.DEVNULL)
            version_line, _ = await proc.communicate()
            version_str: str = version_line.decode().split()[2]
            major, minor = map(int, version_str.split('.')[:2])  # type: int, int
            if (major, minor) < (4, 17):
                # remove warning message of perf from buffer
                await perf_proc.stderr.readline()

        record = dict.fromkeys(event.alias for event in self._perf_config.events)

        while not self._is_stopped:
            ignored = False

            for event in self._perf_config.events:
                raw_line = await perf_proc.stderr.readline()

                line: str = raw_line.decode().strip()
                line_split = line.split(',')

                try:
                    if line_split[1].isdigit():
                        record[event.alias] = int(line_split[1])
                    else:
                        record[event.alias] = float(line_split[1])
                except (IndexError, ValueError):
                    ignored = True

            if not self._is_stopped and not ignored:
                msg = await self.create_message(context, record.copy())
                await BasePipeline.of(context).on_message(context, msg)

        if perf_proc.returncode is None:
            try:
                perf_proc.kill()
            except ProcessLookupError:
                pass

    async def stop(self) -> None:
        self._is_stopped = True

    @property
    async def stopped(self) -> bool:
        return self._is_stopped

    async def create_message(self, context: Context, data: T) -> PerBenchMessage[T]:
        return PerBenchMessage(data, self, BaseBenchmark.of(context))
