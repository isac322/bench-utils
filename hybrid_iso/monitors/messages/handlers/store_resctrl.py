# coding: UTF-8

import asyncio
from pathlib import Path
from typing import Iterable, Optional, Tuple

import aiofiles
from aiofiles.base import AiofilesContextManager

from benchmon.monitors import ResCtrlMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.monitors.resctrl import T as RESCTRL_MSG_TYPE


class StoreResCtrl(BaseHandler):
    _dest_file: Tuple[AiofilesContextManager, ...] = tuple()
    _event_order: Tuple[str, ...]

    @staticmethod
    def _create_afp(bench_name: str, workspace: Path, message: RESCTRL_MSG_TYPE) -> Iterable[int]:
        for core_id in range(len(message)):
            yield aiofiles.open(str(workspace / f'{core_id}_{bench_name}.csv'), mode='w')

    def _generate_value_stream(self, message: RESCTRL_MSG_TYPE, idx: int) -> Iterable[int]:
        for event_name in self._event_order:
            yield message[idx][event_name]

    async def on_message(self, message: PerBenchMessage) -> Optional[PerBenchMessage]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, ResCtrlMonitor):
            return message

        monitor: ResCtrlMonitor = message.source
        benchmark = monitor._benchmark
        workspace: Path = benchmark._bench_config.workspace / 'monitored' / 'resctrl'
        workspace.mkdir(parents=True, exist_ok=True)

        if self._dest_file is tuple():
            self._dest_file = await asyncio.gather(
                    *StoreResCtrl._create_afp(benchmark.identifier, workspace, message.data)
            )
            self._event_order = tuple(message.data[0].keys())

            for dest in self._dest_file:
                await dest.write(','.join(self._event_order) + '\n')

        for idx, dest in enumerate(self._dest_file):
            await dest.write(','.join(map(str, self._generate_value_stream(message.data, idx))) + '\n')

        return message

    async def on_end(self) -> None:
        for afp in self._dest_file:
            afp.close()
