# coding: UTF-8

from pathlib import Path
from typing import Iterable, Optional, Tuple, TypeVar

from aiofile_linux import WriteCmd

from benchmon import Context
from benchmon.benchmark import BaseBenchmark
from benchmon.configs.containers import BenchConfig, Privilege, PrivilegeConfig
from benchmon.context import aio_context
from benchmon.monitors import ResCtrlMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.monitors.resctrl import T as RESCTRL_MSG_TYPE
from benchmon.utils.privilege import drop_privilege

_MT = TypeVar('_MT')


class StoreResCtrl(BaseHandler):
    _event_order: Tuple[str, ...]
    _aio_blocks: Tuple[WriteCmd, ...] = tuple()
    _workspace: Path

    async def on_init(self, context: Context) -> None:
        self._workspace = BenchConfig.of(context).workspace / 'monitored' / 'resctrl'

        privilege_cfg = PrivilegeConfig.of(context).result
        with drop_privilege(privilege_cfg.user, privilege_cfg.group):
            self._workspace.mkdir(parents=True, exist_ok=True)

    def _create_aio_blocks(self, privilege: Privilege, bench_name: str,
                           message: RESCTRL_MSG_TYPE) -> Iterable[WriteCmd]:
        for socket_id in range(len(message)):
            with drop_privilege(privilege.user, privilege.group):
                file = open(str(self._workspace / f'{socket_id}_{bench_name}.csv'), mode='w')
            yield WriteCmd(file, '')

    def _generate_value_stream(self, message: RESCTRL_MSG_TYPE, idx: int) -> Iterable[int]:
        for event_name in self._event_order:
            yield message[idx][event_name]

    async def on_message(self, context: Context, message: PerBenchMessage[_MT]) -> Optional[PerBenchMessage[_MT]]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, ResCtrlMonitor):
            return message

        if self._aio_blocks is tuple():
            benchmark = BaseBenchmark.of(context)
            privilege_cfg = PrivilegeConfig.of(context).result

            self._aio_blocks = tuple(self._create_aio_blocks(privilege_cfg, benchmark.identifier, message.data))
            self._event_order = tuple(message.data[0].keys())

            for block in self._aio_blocks:
                block.buffer = (','.join(self._event_order) + '\n').encode()
            await aio_context().submit(*self._aio_blocks)
            for block in self._aio_blocks:
                block.offset += len(block.buffer)

        for idx, block in enumerate(self._aio_blocks):
            block.buffer = (','.join(map(str, self._generate_value_stream(message.data, idx))) + '\n').encode()
        await aio_context().submit(*self._aio_blocks)
        for block in self._aio_blocks:
            block.offset += len(block.buffer)

        return message

    async def on_end(self, context: Context) -> None:
        for block in self._aio_blocks:
            block.file.close()
