# coding: UTF-8

from pathlib import Path
from typing import Iterable, Optional, Tuple

from aiofile_linux import AIOContext, WriteCmd

from benchmon import Context
from benchmon.benchmark import BaseBenchmark
from benchmon.monitors import ResCtrlMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.monitors.resctrl import T as RESCTRL_MSG_TYPE


class StoreResCtrl(BaseHandler):
    _event_order: Tuple[str, ...]
    _aio_context: AIOContext
    _aio_blocks: Tuple[WriteCmd, ...] = tuple()

    async def on_init(self, context: Context) -> None:
        # FIXME: hard coded
        self._aio_context = AIOContext(4)

    @staticmethod
    def _create_aio_blocks(bench_name: str, workspace: Path, message: RESCTRL_MSG_TYPE) -> Iterable[WriteCmd]:
        for socket_id in range(len(message)):
            file = open(str(workspace / f'{socket_id}_{bench_name}.csv'), mode='w')
            yield WriteCmd(file, '')

    def _generate_value_stream(self, message: RESCTRL_MSG_TYPE, idx: int) -> Iterable[int]:
        for event_name in self._event_order:
            yield message[idx][event_name]

    async def on_message(self, context: Context, message: PerBenchMessage) -> Optional[PerBenchMessage]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, ResCtrlMonitor):
            return message

        benchmark = BaseBenchmark.of(context)
        workspace: Path = benchmark._bench_config.workspace / 'monitored' / 'resctrl'
        workspace.mkdir(parents=True, exist_ok=True)

        if self._aio_blocks is tuple():
            self._aio_blocks = tuple(self._create_aio_blocks(benchmark.identifier, workspace, message.data))
            self._event_order = tuple(message.data[0].keys())

            for block in self._aio_blocks:
                block.buffer = (','.join(self._event_order) + '\n').encode()
            await self._aio_context.submit(*self._aio_blocks)
            for block in self._aio_blocks:
                block.offset += len(block.buffer)

        for idx, block in enumerate(self._aio_blocks):
            block.buffer = (','.join(map(str, self._generate_value_stream(message.data, idx))) + '\n').encode()
        await self._aio_context.submit(*self._aio_blocks)
        for block in self._aio_blocks:
            block.offset += len(block.buffer)

        return message

    async def on_end(self, context: Context) -> None:
        for block in self._aio_blocks:
            block.file.close()
        self._aio_context.close()
