# coding: UTF-8

import asyncio
import re
from itertools import chain
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, Mapping, Optional, Tuple

import aiofiles
from aiofiles.base import AiofilesContextManager
from psutil import Process

from .handlers.base_handler import BaseHandler
from .oneshot_monitor import OneShotMonitor


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

    def __init__(self, handlers: Iterable[BaseHandler], interval: int,
                 grp_name: str = '', parent_pid: int = None) -> None:
        super().__init__(handlers, interval)

        self._group_name = grp_name
        self._group_path = ResCtrlMonitor.mount_point / self._group_name
        self._monitoring_pid = parent_pid

        # tuple of each feature monitors for each socket
        self._monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...] = tuple(
                dict.fromkeys(
                        self._group_path / 'mon_data' / mon.name / feature for feature in ResCtrlMonitor.mon_features
                )
                for mon in ResCtrlMonitor._mon_names
        )

    @staticmethod
    def _get_all_children(pid: int) -> FrozenSet[int]:
        target = Process(pid)
        all_children = ((t.id for t in proc.threads()) for proc in target.children(recursive=True))
        return frozenset(chain(*all_children, map(lambda t: t.id, target.threads())))

    async def on_init(self) -> None:
        async def write_to_tasks(pid: int) -> None:
            write_proc: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
                    'sudo', 'tee', str(self._group_path / 'tasks'),
                    encoding='ASCII',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.DEVNULL)

            await write_proc.communicate(str(pid).encode())

        if not ResCtrlMonitor.mount_point.is_dir():
            raise PermissionError(f'resctrl is not mounted on {ResCtrlMonitor.mount_point.absolute()}')

        proc = await asyncio.create_subprocess_exec('sudo', 'mkdir', str(self._group_path), '-p')
        await proc.wait()

        family_pids = ResCtrlMonitor._get_all_children(self._monitoring_pid)
        await asyncio.wait(tuple(map(write_to_tasks, family_pids)))

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
