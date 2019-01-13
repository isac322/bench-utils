# coding: UTF-8

from typing import Iterable, Optional, Tuple, Union

import aiofiles
from aiofiles.base import AiofilesContextManager

from benchmon.monitors import PerfMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.monitors.perf import T as PERF_MSG_TYPE


class StorePerf(BaseHandler):
    _dest_file: Optional[AiofilesContextManager] = None
    _event_order: Tuple[str, ...]

    def _generate_value_stream(self, message: PERF_MSG_TYPE) -> Iterable[Union[float, int]]:
        for event_name in self._event_order:
            yield message[event_name]

    async def on_message(self, message: PerBenchMessage) -> Optional[PerBenchMessage]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, PerfMonitor):
            return message

        perf_monitor: PerfMonitor = message.source

        if self._dest_file is None:
            benchmark = perf_monitor._benchmark
            workspace = benchmark._bench_config.workspace / 'monitored'
            workspace.mkdir(parents=True, exist_ok=True)

            self._dest_file = await aiofiles.open(str(workspace / f'perf_{benchmark.identifier}.csv'), mode='w')
            self._event_order = tuple(perf_monitor._perf_config.event_names)
            await self._dest_file.write(','.join(self._event_order) + '\n')

        await self._dest_file.write(','.join(map(str, self._generate_value_stream(message.data))) + '\n')

        return message

    async def on_end(self) -> None:
        if self._dest_file is not None:
            self._dest_file.close()
