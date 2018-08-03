# coding: UTF-8

import asyncio
import re
from itertools import chain
from pathlib import Path
from typing import FrozenSet, Iterable, Mapping, Tuple

from aiofile import AIOFile, LineReader
from psutil import Process

from monitors.handlers.base_handler import BaseHandler
from monitors.oneshot_monitor import OneShotMonitor


class ResctrlMonitor(OneShotMonitor[Tuple[Mapping[str, int], ...]]):
    mount_point = Path('/sys/fs/resctrl')
    _l3_pattern = re.compile('mon_L3_(\d+)')
    mon_features = (mount_point / 'info' / 'L3_MON' / 'mon_features').read_text('ASCII').split()

    def __init__(self, interval: int, handlers: Iterable[BaseHandler],
                 grp_name: str = '', parent_pid: int = None) -> None:
        super().__init__(interval, handlers)
        self._group_name = grp_name
        self._group_path = ResctrlMonitor.mount_point / self._group_name
        self._monitoring_pid = parent_pid

        # filter L3 related monitors and sort by name (currently same as socket number)
        mon_names = sorted(
                filter(
                        lambda m: ResctrlMonitor._l3_pattern.match(m.name),
                        (ResctrlMonitor.mount_point / 'mon_data').iterdir()
                )
        )

        # tuple of each feature monitors for each socket
        self._mons = tuple(
                tuple(self._group_path / 'mon_data' / mon.name / feature for feature in ResctrlMonitor.mon_features)
                for mon in mon_names
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

        if not ResctrlMonitor.mount_point.is_dir():
            raise PermissionError(f'resctrl is not mounted on {ResctrlMonitor.mount_point.absolute()}')

        proc = await asyncio.create_subprocess_exec('sudo', 'mkdir', str(self._group_path), '-p')
        await proc.wait()

        family_pids = ResctrlMonitor._get_all_children(self._monitoring_pid)
        await asyncio.wait(tuple(map(write_to_tasks, family_pids)))

    @staticmethod
    async def _read_file(path: Path) -> Tuple[str, int]:
        async with AIOFile(str(path)) as afp:
            line: str = await LineReader(afp).readline()
            return path.name, int(line)

    async def monitor_once(self) -> Mapping[str, Tuple[Mapping[str, int], ...]]:
        data = tuple(
                map(dict,
                    await asyncio.gather(*(
                        asyncio.gather(*(
                            self._read_file(mon) for mon in mons
                        ))
                        for mons in self._mons))
                    )
        )

        return dict(resctrl=data)

    async def on_destroy(self) -> None:
        await super().on_destroy()
        proc = await asyncio.create_subprocess_exec('sudo', 'rmdir', str(self._group_path))
        await proc.wait()
