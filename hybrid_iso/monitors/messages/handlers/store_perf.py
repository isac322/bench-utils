# coding: UTF-8

from typing import Iterable, Optional, TextIO, Tuple, Union

from benchmon import Context
from benchmon.benchmark import BaseBenchmark
from benchmon.configs.containers import BenchConfig, PerfConfig
from benchmon.monitors import PerfMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.monitors.perf import T as PERF_MSG_TYPE


class StorePerf(BaseHandler):
    _dest_file: Optional[TextIO] = None
    _event_order: Tuple[str, ...]

    def _generate_value_stream(self, message: PERF_MSG_TYPE) -> Iterable[Union[float, int]]:
        for event_name in self._event_order:
            yield message[event_name]

    async def on_init(self, context: Context) -> None:
        benchmark = BaseBenchmark.of(context)
        workspace = BenchConfig.of(context).workspace / 'monitored' / 'perf'
        workspace.mkdir(parents=True, exist_ok=True)

        # TODO: compare between open and aiofile_linux.
        #  (maybe open() is better when writing small amount of contents to a file at a time)
        self._dest_file = (workspace / f'{benchmark.identifier}.csv').open(mode='w')
        self._event_order = tuple(PerfConfig.of(context).event_names)
        self._dest_file.write(','.join(self._event_order) + '\n')

    async def on_message(self, context: Context, message: PerBenchMessage) -> Optional[PerBenchMessage]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, PerfMonitor):
            return message

        self._dest_file.write(','.join(map(str, self._generate_value_stream(message.data))) + '\n')

        return message

    async def on_end(self, context: Context) -> None:
        if self._dest_file is not None:
            self._dest_file.close()
