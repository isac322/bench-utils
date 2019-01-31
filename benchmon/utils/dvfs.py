# coding: UTF-8

"""
:mod:`dvfs` -- Linux의 DVFS API wrapper
=======================================================

`/sys/devices/system/cpu` 에 있는 DVFS에 관한 Linux API wrapper

.. todo::
    * per-core DVFS지원 check

.. module:: benchmon.utils.dvfs
    :synopsis: Linux의 DVFS API wrapper
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

import asyncio
from typing import Iterable, Tuple

import aiofiles


async def set_max_freq(core_id: int, freq: int) -> None:
    """
    `core_id` 번 코어의 최대 주파수를 `freq` MHz로 설정한다.

    .. note::
        per-core DVFS를 지원하지 않는 CPU라고 할지라도 API에 접근 가능하기 때문에 따로 체크가 필요하다

    :param core_id: 주파수를 바꿀 CPU 코어 번호
    :type core_id: int
    :param freq: 바꿀 주파수 값
    :type freq: int
    """
    proc = await asyncio.create_subprocess_exec(
            'sudo', 'tee', f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL)

    await proc.communicate(f'{freq}\n'.encode())


async def set_max_freqs(core_ids: Iterable[int], freq: int) -> None:
    """
    `core_ids` 번 코어들의 최대 주파수를 `freq` MHz로 설정한다.

    .. note::
        per-core DVFS를 지원하지 않는 CPU라고 할지라도 API에 접근 가능하기 때문에 따로 체크가 필요하다

    :param core_ids: 주파수를 바꿀 CPU 코어 번호들
    :type core_ids: typing.Iterable[int]
    :param freq: 바꿀 주파수 값
    :type freq: int
    """
    target_files = (
        f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq'
        for core_id in core_ids
    )

    proc = await asyncio.create_subprocess_exec(
            'sudo', 'tee', *target_files,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL)

    await proc.communicate(f'{freq}\n'.encode())


async def read_max_freq(core_id: int) -> int:
    """
    `core_id` 번 코어의 최대 주파수를 읽어온다

    :param core_id: 최대 주파수를 구할 코어 번호
    :type core_id: int
    :return: 코어의 최대 주파수
    :rtype: int
    """
    async with aiofiles.open(f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq') as afp:
        line: str = await afp.readline()
        return int(line)


async def read_max_freqs(core_ids: Iterable[int]) -> Tuple[int, ...]:
    """
    `core_ids` 번 코어들의 최대 주파수를 읽어온다

    :param core_ids: 최대 주파수를 구할 코어 번호
    :type core_ids: typing.Iterable[int]
    :return: 코어들의 최대 주파수
    :rtype: typing.Tuple[int, ...]
    """
    return await asyncio.gather(*map(read_max_freq, core_ids))
