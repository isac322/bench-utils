# coding: UTF-8

from __future__ import annotations

import asyncio
import re
from itertools import chain
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Tuple

import aiofiles
from aiofiles.base import AiofilesContextManager

from . import MonitorData
from .base_builder import BaseBuilder
from .messages import BaseMessage
from .oneshot_monitor import OneShotMonitor
from ..benchmark import Benchmark
from ..containers import HandlerConfig


class ResCtrlMonitor(OneShotMonitor[Tuple[Mapping[str, int], ...]]):
    mount_point = Path('/sys/fs/resctrl')
    mon_features = (mount_point / 'info' / 'L3_MON' / 'mon_features').read_text('ASCII').split()

    # filter L3 related monitors and sort by name (currently same as socket number)
    _mon_names = sorted(
            filter(
                    lambda m: re.match('mon_L3_(\d+)', m.name),
                    (mount_point / 'mon_data').iterdir()
            )
    )

    def __init__(self, emitter: Callable[[BaseMessage], None], interval: int, bench: Benchmark = None) -> None:
        super().__init__(emitter, interval)

        self._benchmark: Benchmark = bench
        self._group_path: Path = ResCtrlMonitor.mount_point

        # tuple of each feature monitors for each socket
        self._monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...] = tuple()

    async def _write_to_tasks(self, pid: int) -> None:
        write_proc: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
                'sudo', 'tee', str(self._group_path / 'tasks'),
                encoding='ASCII',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL)

        await write_proc.communicate(str(pid).encode())

    async def on_init(self) -> None:
        await super().on_init()

        if self._benchmark is not None:
            self._group_path = ResCtrlMonitor.mount_point / self._benchmark.benchmark_name

        # tuple of each feature monitors for each socket
        self._monitors = tuple(
                dict.fromkeys(
                        self._group_path / 'mon_data' / mon.name / feature for feature in ResCtrlMonitor.mon_features
                )
                for mon in ResCtrlMonitor._mon_names
        )

        if not ResCtrlMonitor.mount_point.is_dir():
            raise PermissionError(f'resctrl is not mounted on {ResCtrlMonitor.mount_point.absolute()}')

        proc = await asyncio.create_subprocess_exec('sudo', 'mkdir', str(self._group_path), '-p')
        await proc.wait()

        if self._benchmark is not None:
            await asyncio.wait(tuple(map(self._write_to_tasks, self._benchmark.all_child_tid())))

        async def open_file_async(monitor_dict: Dict[Path, AiofilesContextManager]):
            for file_path in monitor_dict:
                monitor_dict[file_path] = await aiofiles.open(file_path)

        await asyncio.wait(tuple(open_file_async(mon) for mon in self._monitors))

    @staticmethod
    async def _read_file(arg: Tuple[Path, AiofilesContextManager]) -> Tuple[str, int]:
        path, monitor = arg
        await monitor.seek(0)
        return path.name, int(await monitor.readline())

    async def monitor_once(self) -> Mapping[str, Tuple[Mapping[str, int], ...]]:
        data = tuple(
                map(dict,
                    await asyncio.gather(*(
                        asyncio.gather(*map(ResCtrlMonitor._read_file, mons.items()))
                        for mons in self._monitors))
                    )
        )

        return dict(resctrl=data)

    async def create_message(self, data: Mapping[str, MonitorData]) -> BaseMessage:
        pass

    async def on_destroy(self) -> None:
        await super().on_destroy()

        proc = await asyncio.create_subprocess_exec('sudo', 'rmdir', str(self._group_path))
        await proc.wait()

        await asyncio.wait(tuple(
                chain(*(
                    (m.close() for m in mons.values())
                    for mons in self._monitors
                ))
        ))

    class Builder(BaseBuilder['ResCtrlMonitor']):
        def _build_handler(self, handler_config: HandlerConfig) -> None:
            pass

        async def _finalize(self) -> ResCtrlMonitor:
            pass
