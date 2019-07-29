# coding: UTF-8

"""
:mod:`hyperthreading` -- Linux의 Hyper-Threading API wrapper
============================================================

`/sys/devices/system/cpu/online` 을 사용하여 Hyper-Threading을 조정한다.

.. note::
    Hyper-Threading만을 위한 API를 사용한것이 아니기 때문에 사용시 주의가 필요하다

.. module:: benchmon.utils.hyperthreading
    :synopsis: Linux의 Hyper-Threading API wrapper
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

import contextlib
import os
from typing import Set

from .ranges import Ranges


@contextlib.contextmanager
def hyper_threading_guard(ht_flag: bool) -> None:
    """
    :keyword:`async with` 과 사용되며, 그 블럭 안에서 `ht_flag` 에 따라서 Hyper-Threading을 끄는것을 보장한다.

    .. todo::
        코드에서 :func:`print` 를 :class:`logging.Logger` 로 교체

    :param ht_flag: Hyper-Threading을 끌것인가 말것인가
    :type ht_flag: bool
    """

    if not ht_flag:
        with open('/sys/devices/system/cpu/online') as fp:
            raw_input: str = fp.readline()

        online_cores: Ranges = Ranges.from_str(raw_input)

        print('disabling Hyper-Threading...')

        logical_cores: Set[int] = set()

        for core_id in online_cores:
            with open(f'/sys/devices/system/cpu/cpu{core_id}/topology/thread_siblings_list') as fp:
                line: str = fp.readline()
                logical_cores.update(map(int, line.strip().split(',')[1:]))

        for core_id in logical_cores:
            fd = os.open(f'/sys/devices/system/cpu/cpu{core_id}/online', os.O_WRONLY)
            os.write(fd, b'0')
            os.close(fd)

        print('Hyper-Threading is disabled.')
        yield
        print('restoring Hyper-Threading...')

        for core_id in logical_cores:
            fd = os.open(f'/sys/devices/system/cpu/cpu{core_id}/online', os.O_WRONLY)
            os.write(fd, b'1')
            os.close(fd)

    else:
        yield
