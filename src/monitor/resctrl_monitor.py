# coding: UTF-8

import asyncio
import re
from pathlib import Path
from typing import Iterable, Mapping, Tuple

import aiofiles

from monitor.handlers.base_handler import BaseHandler
from monitor.oneshot_monitor import OneShotMonitor


class ResctrlMonitor(OneShotMonitor[Tuple[Mapping[str, int], ...]]):
    mount_point = Path('/sys/fs/resctrl')
    _l3_pattern = re.compile('mon_L3_(\d+)')
    mon_features = (mount_point / 'info' / 'L3_MON' / 'mon_features').read_text('ASCII').split()

    def __init__(self, interval: int, handlers: Iterable[BaseHandler],
                 grp_name: str = '', parent_pid: int = None) -> None:
        super().__init__(interval, handlers)
        self._group_name = grp_name
        self._group_path = self.mount_point / self._group_name
        self._monitoring_pid = parent_pid

        # filter L3 related monitors and sort by name (currently same as socket number)
        mons = sorted(
                filter(
                        lambda m: self._l3_pattern.match(m.name),
                        (self._group_path / 'mon_data').iterdir()
                )
        )

        # tuple of each feature monitors for each socket
        self._mons = tuple(
                tuple(mon / feature for feature in self.mon_features) for mon in mons
        )

    async def on_init(self) -> None:
        if not self.mount_point.is_dir():
            raise PermissionError(f'resctrl is not mounted on {self.mount_point.absolute()}')

        proc = await asyncio.create_subprocess_exec('sudo', 'mkdir', str(self._group_path), '-p')
        await proc.wait()

        # TODO: fetching all children pid of `self._monitoring_pid` and append to `tasks` file

    @staticmethod
    async def _read_file(path: Path) -> Tuple[str, int]:
        async with aiofiles.open(path) as fp:
            line: str = await fp.readline()
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
        proc = await asyncio.create_subprocess_exec('sudo', 'rmdir', str(self._group_path))
        await proc.wait()
