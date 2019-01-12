# coding: UTF-8

import asyncio
import contextlib
from typing import Set

import aiofiles

from .hyphen import convert_to_set


@contextlib.asynccontextmanager
async def hyper_threading_guard(ht_flag: bool):
    async with aiofiles.open('/sys/devices/system/cpu/online') as afp:
        raw_input: str = await afp.readline()

    online_cores: Set[int] = convert_to_set(raw_input)

    if not ht_flag:
        print('disabling Hyper-Threading...')

        logical_cores: Set[int] = set()

        async def _read_siblings(core: int) -> None:
            async with aiofiles.open(f'/sys/devices/system/cpu/cpu{core}/topology/thread_siblings_list') as fp:
                line: str = await fp.readline()
                logical_cores.update(map(int, line.strip().split(',')[1:]))

        await asyncio.wait(tuple(_read_siblings(core_id) for core_id in online_cores))

        files_to_write = (f'/sys/devices/system/cpu/cpu{core_id}/online' for core_id in logical_cores)
        proc = await asyncio.create_subprocess_exec('sudo', 'tee', *files_to_write,
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.DEVNULL)
        await proc.communicate('0'.encode())

        print('Hyper-Threading is disabled.')

    yield

    if not ht_flag:
        print('restoring Hyper-Threading...')

        files_to_write = (f'/sys/devices/system/cpu/cpu{core_id}/online' for core_id in online_cores if
                          core_id is not 0)
        proc = await asyncio.create_subprocess_exec('sudo', 'tee', *files_to_write,
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.DEVNULL)
        await proc.communicate('1'.encode())
