# coding: UTF-8

"""
:mod:`hyperthreading` -- Linux의 Hyper-Threading API wrapper
============================================================

`/sys/devices/system/cpu/online` 을 사용하여 Hyper-Threading을 조정한다.

.. note::
    Hyper-Threading만을 위한 API를 사용한것이 아니기 때문에 사용시 주의가 필요하다

.. module:: bench_toolbox.utils.hyperthreading
    :synopsis: Linux의 Hyper-Threading API wrapper
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

import asyncio
import contextlib
from typing import Set

import aiofiles

from .hyphen import convert_to_set


@contextlib.asynccontextmanager
async def hyper_threading_guard(ht_flag: bool) -> None:
    """
    :keyword:`async with` 과 사용되며, 그 블럭 안에서 `ht_flag` 에 따라서 Hyper-Threading을 끄는것을 보장한다.

    .. todo::
        코드에서 :keyword:`print` 를 :class:`logging.Logger` 로 교체

    :param ht_flag: Hyper-Threading을 끌것인가 말것인가
    :type ht_flag: bool
    """
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
