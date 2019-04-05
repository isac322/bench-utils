# coding: UTF-8

from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING, TextIO, Tuple, Union

from benchmon.benchmark import BaseBenchmark
from benchmon.configs.containers import PrivilegeConfig
from benchmon.monitors import PerfMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.utils.privilege import drop_privilege

if TYPE_CHECKING:
    from benchmon import Context
    from benchmon.monitors.messages import BaseMessage
    from benchmon.monitors.perf import DAT_TYPE as PERF_MSG_TYPE


class StorePerf(BaseHandler):
    _dest_file: Optional[TextIO] = None
    _event_order: Tuple[str, ...]

    def _generate_value_stream(self, message: PERF_MSG_TYPE) -> Iterable[Union[float, int]]:
        for event_name in self._event_order:
            yield message[event_name]

    async def on_init(self, context: Context) -> None:
        benchmark = BaseBenchmark.of(context)
        workspace = benchmark.bench_config.workspace / 'monitored' / 'perf'

        privilege_cfg = PrivilegeConfig.of(context).result
        with drop_privilege(privilege_cfg.user, privilege_cfg.group):
            workspace.mkdir(parents=True, exist_ok=True)

            # TODO: compare between open and aiofile_linux.
            #  (maybe open() is better when writing small amount of contents to a file at a time)
            self._dest_file = (workspace / f'{benchmark.identifier}.csv').open(mode='w')

        # FIXME: None check
        perf_monitor = PerfMonitor.of(context)
        self._event_order = tuple(perf_monitor.config.event_names)
        self._dest_file.write(','.join(self._event_order) + '\n')

    async def on_message(self, context: Context, message: BaseMessage[PERF_MSG_TYPE]) -> BaseMessage[PERF_MSG_TYPE]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, PerfMonitor):
            return message

        self._dest_file.write(','.join(map(str, self._generate_value_stream(message.data))) + '\n')

        return message

    async def on_end(self, context: Context) -> None:
        if self._dest_file is not None:
            self._dest_file.close()
