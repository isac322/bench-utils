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

import os
from typing import Iterable, Tuple


def set_max_freq(core_id: int, freq: int) -> None:
    """
    `core_id` 번 코어의 최대 주파수를 `freq` MHz로 설정한다.

    .. note::
        per-core DVFS를 지원하지 않는 CPU라고 할지라도 API에 접근 가능하기 때문에 따로 체크가 필요하다

    :param core_id: 주파수를 바꿀 CPU 코어 번호
    :type core_id: int
    :param freq: 바꿀 주파수 값
    :type freq: int
    """
    with open(f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq', 'w') as fp:
        fp.write(f'{freq}\n')


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
    encoded_freq = f'{freq}\n'.encode()
    for core_id in core_ids:
        fd = os.open(f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq', os.O_WRONLY)
        os.write(fd, encoded_freq)
        os.close(fd)


def read_max_freq(core_id: int) -> int:
    """
    `core_id` 번 코어의 최대 주파수를 읽어온다

    :param core_id: 최대 주파수를 구할 코어 번호
    :type core_id: int
    :return: 코어의 최대 주파수
    :rtype: int
    """
    with open(f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq') as fp:
        line: str = fp.readline()
        return int(line)


def read_max_freqs(core_ids: Iterable[int]) -> Tuple[int, ...]:
    """
    `core_ids` 번 코어들의 최대 주파수를 읽어온다

    :param core_ids: 최대 주파수를 구할 코어 번호
    :type core_ids: typing.Iterable[int]
    :return: 코어들의 최대 주파수
    :rtype: typing.Tuple[int, ...]
    """
    return tuple(read_max_freq(core_id) for core_id in core_ids)
