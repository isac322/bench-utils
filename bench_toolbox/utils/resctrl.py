# coding: UTF-8

import asyncio
import re
from itertools import chain
from pathlib import Path
from typing import ClassVar, Dict, Iterable, Mapping, Optional, Tuple

import aiofiles
from aiofiles.base import AiofilesContextManager

from .asyncio_subprocess import check_run


def mask_to_bits(mask: str) -> int:
    cnt = 0
    num = int(mask, 16)
    while num is not 0:
        cnt += 1
        num >>= 1
    return cnt


def bits_to_mask(bits: int) -> str:
    return f'{bits:x}'


async def _open_file_async(monitor_dict: Dict[Path, AiofilesContextManager]) -> None:
    for file_path in monitor_dict:
        monitor_dict[file_path] = await aiofiles.open(file_path)


async def _read_file(path: Path, monitor: AiofilesContextManager) -> Tuple[str, int]:
    await monitor.seek(0)
    return path.name, int(await monitor.readline())


class ResCtrl:
    MOUNT_POINT: ClassVar[Path] = Path('/sys/fs/resctrl')
    FEATURES: ClassVar[Tuple[str, ...]] = tuple(
            (MOUNT_POINT / 'info' / 'L3_MON' / 'mon_features').read_text('ASCII').strip().split()
    )

    # filter L3 related monitors and sort by name (currently same as socket number)
    _MON_NAMES: ClassVar[Tuple[str, ...]] = tuple(sorted(
            map(
                    lambda x: x.name,
                    filter(
                            lambda m: re.match('mon_L3_(\d+)', m.name),
                            MOUNT_POINT.joinpath('mon_data').glob('mon_L3_*')
                    )
            )
    ))

    MAX_MASK: ClassVar[str] = MOUNT_POINT.joinpath('info/L3/cbm_mask').read_text(encoding='ASCII').strip()
    MAX_BITS: ClassVar[int] = mask_to_bits(MAX_MASK)
    MIN_BITS: ClassVar[int] = int((MOUNT_POINT / 'info' / 'L3' / 'min_cbm_bits').read_text())
    MIN_MASK: ClassVar[str] = bits_to_mask(MIN_BITS)

    _group_name: str
    _group_path: Path
    _prepare_read: bool = False
    # tuple of each feature monitors for each socket
    _monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...]

    def __init__(self) -> None:
        self.group_name = str()

    @property
    def group_name(self) -> str:
        return self._group_name

    @group_name.setter
    def group_name(self, new_name) -> None:
        self._group_name = new_name
        self._group_path = ResCtrl.MOUNT_POINT / new_name
        self._monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...] = tuple(
                dict.fromkeys(
                        self._group_path / 'mon_data' / mon_name / feature for feature in ResCtrl.FEATURES
                )
                for mon_name in ResCtrl._MON_NAMES
        )

    async def create_group(self) -> None:
        await check_run('sudo', 'mkdir', '-p', str(self._group_path))

    async def prepare_to_read(self) -> None:
        if self._prepare_read:
            raise AssertionError('The ResCtrl object is already prepared to read.')

        self._prepare_read = True
        await asyncio.wait(tuple(map(_open_file_async, self._monitors)))

    async def add_task(self, pid: int) -> None:
        await check_run('sudo', 'tee', '-a', str(self._group_path / 'tasks'),
                        input=str(pid).encode(),
                        stdout=asyncio.subprocess.DEVNULL)

    async def add_tasks(self, pids: Iterable[int]) -> None:
        for pid in pids:
            await self.add_task(pid)

    async def assign_llc(self, *masks: str) -> None:
        masks = (f'{i}={m}' for i, m in enumerate(masks))
        schemata = 'L3:{}\n'.format(';'.join(masks))

        await check_run('sudo', 'tee', str(self._group_path / 'schemata'),
                        input=schemata.encode(),
                        stdout=asyncio.subprocess.DEVNULL)

    @staticmethod
    def gen_mask(start: int, end: Optional[int] = None) -> str:
        if end is None or end > ResCtrl.MAX_BITS:
            end = ResCtrl.MAX_BITS

        if start < 0:
            raise ValueError('start must be greater than 0')

        return format(((1 << (end - start)) - 1) << (ResCtrl.MAX_BITS - end), 'x')

    async def read(self) -> Tuple[Mapping[str, int], ...]:
        if not self._prepare_read:
            raise AssertionError('The ResCtrl object is not ready to read.')

        return tuple(
                map(dict,
                    await asyncio.gather(*(
                        asyncio.gather(*(_read_file(k, v) for k, v in mons.items()))
                        for mons in self._monitors))
                    )
        )

    async def end_read(self) -> None:
        if not self._prepare_read:
            raise AssertionError('The ResCtrl object is not ready to read.')

        await asyncio.wait(tuple(
                chain(*(
                    (mon.close() for mon in mons.values())
                    for mons in self._monitors
                ))
        ))

    async def delete(self) -> None:
        if self._prepare_read:
            await self.end_read()

        if self._group_name is str():
            raise PermissionError('Can not remove root directory of resctrl')

        await check_run('sudo', 'rmdir', str(self._group_path))
