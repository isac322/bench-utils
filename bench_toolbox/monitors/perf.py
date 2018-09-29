# coding: UTF-8

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Coroutine, Mapping, Type, Union

from .base import BaseMonitor
from .base_builder import BaseBuilder
from .messages import BaseMessage
from .messages.per_bench import PerBenchMessage
from ..benchmark import BaseBenchmark
from ..containers import PerfConfig

T = Mapping[str, Union[int, float]]


class PerfMonitor(BaseMonitor[T]):
    _perf_config: PerfConfig
    _benchmark: BaseBenchmark
    _is_stopped: bool = False

    def __new__(cls: Type[PerfMonitor],
                emitter: Callable[[BaseMessage[T]], Coroutine[None, None, None]],
                benchmark: BaseBenchmark,
                perf_config: PerfConfig) -> PerfMonitor:
        obj: PerfMonitor = super().__new__(cls, emitter)

        obj._perf_config = perf_config
        obj._benchmark = benchmark

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def _monitor(self) -> None:
        logger = logging.getLogger(__name__)
        perf_proc = await asyncio.create_subprocess_exec(
                'perf', 'stat', '-e', self._perf_config.event_str,
                '-p', str(self._benchmark.pid), '-x', ',', '-I', str(self._perf_config.interval),
                stderr=asyncio.subprocess.PIPE)

        if self._perf_config.interval < 100:
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
                except (IndexError, ValueError) as e:
                    ignored = True
                    logger.debug(f'a line that perf printed was ignored due to following exception : {e}'
                                 f' and the line is : {line}')

            if not self._is_stopped and not ignored:
                msg = await self.create_message(record.copy())
                await self._emitter(msg)

        if perf_proc.returncode is None:
            try:
                perf_proc.kill()
            except ProcessLookupError as e:
                logger.debug(f'The perf killed before explicit killing : {e}')

    async def stop(self) -> None:
        self._is_stopped = True

    @property
    async def stopped(self) -> bool:
        return self._is_stopped

    async def create_message(self, data: T) -> PerBenchMessage[T]:
        return PerBenchMessage(data, self, self._benchmark)

    class Builder(BaseBuilder['PerfMonitor']):
        _perf_config: PerfConfig

        def __init__(self, perf_config: PerfConfig) -> None:
            super().__init__()
            self._perf_config = perf_config

        def _finalize(self) -> PerfMonitor:
            return PerfMonitor.__new__(PerfMonitor, self._cur_emitter, self._cur_bench, self._perf_config)
