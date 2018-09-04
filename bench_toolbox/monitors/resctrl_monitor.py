# coding: UTF-8

from __future__ import annotations

import asyncio
import re
from itertools import chain
from pathlib import Path
from typing import Callable, ClassVar, Coroutine, Dict, List, Mapping, Optional, Tuple, Type

import aiofiles
from aiofiles.base import AiofilesContextManager

from .base_builder import BaseBuilder
from .iteration_dependent_monitor import IterationDependentMonitor
from .messages import BaseMessage
from .messages.per_bench_message import PerBenchMessage
from .messages.system_message import SystemMessage
from ..benchmark import Benchmark

T = Tuple[Mapping[str, int], ...]


class ResCtrlMonitor(IterationDependentMonitor[T]):
    mount_point: ClassVar[Path] = Path('/sys/fs/resctrl')
    mon_features: ClassVar[List[str]] = (mount_point / 'info' / 'L3_MON' / 'mon_features').read_text('ASCII').split()

    # filter L3 related monitors and sort by name (currently same as socket number)
    _mon_names: ClassVar[List[Path]] = sorted(
            filter(
                    lambda m: re.match('mon_L3_(\d+)', m.name),
                    (mount_point / 'mon_data').iterdir()
            )
    )

    _benchmark: Optional[Benchmark]
    _group_path: Path
    # tuple of each feature monitors for each socket
    _monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...]

    def __new__(cls: Type[ResCtrlMonitor],
                emitter: Callable[[BaseMessage], Coroutine[None, None, None]],
                interval: int,
                bench: Benchmark = None) -> ResCtrlMonitor:
        obj: ResCtrlMonitor = super().__new__(cls, emitter, interval)

        obj._benchmark = bench
        obj._group_path = ResCtrlMonitor.mount_point
        obj._monitors = tuple()

        return obj

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError('Use ResCtrlMonitor.Builder to instantiate ResCtrlMonitor')

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

    async def monitor_once(self) -> T:
        return tuple(
                map(dict,
                    await asyncio.gather(*(
                        asyncio.gather(*map(ResCtrlMonitor._read_file, mons.items()))
                        for mons in self._monitors))
                    )
        )

    def calc_diff(self, before: T, after: T) -> T:
        result: List[Dict[str, int]] = list()

        for idx, d in enumerate(after):
            merged: Dict[str, int] = dict()

            for k, v in d:
                if k != 'llc_occupancy':
                    v -= before[idx][k]

                merged[k] = v
            result.append(merged)

        return tuple(result)

    async def create_message(self, data: T) -> BaseMessage[T]:
        if self._benchmark is None:
            return SystemMessage(data, self)
        else:
            return PerBenchMessage(data, self, self._benchmark)

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
        _interval: int

        def __init__(self, interval: int) -> None:
            super().__init__()
            self._interval = interval

        async def _finalize(self) -> ResCtrlMonitor:
            return ResCtrlMonitor.__new__(ResCtrlMonitor, self._cur_emitter, self._interval, self._cur_bench)
