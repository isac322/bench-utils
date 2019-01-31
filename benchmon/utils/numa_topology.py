# coding: UTF-8

"""
:mod:`numa_topology` -- Linux의 Node API wrapper
============================================================

`/sys/devices/system/node` 에서 제공하는 정보들을 가공한다

.. note::
    완벽하게 정리된 구현이 아니므로 사용에 주의가 필요하다

.. module:: bench_toolbox.utils.numa_topology
    :synopsis: Linux의 Node API wrapper
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>, Yoonsung Nam <ysnam@dcslab.snu.ac.kr>
"""

from pathlib import Path
from typing import Dict, Mapping, Set

from .hyphen import convert_to_set

_BASE_PATH: Path = Path('/sys/devices/system/node')


def get_mem_topo() -> Set[int]:
    has_memory_path = _BASE_PATH / 'has_memory'

    with has_memory_path.open() as fp:
        line: str = fp.readline()
        mem_topo = convert_to_set(line)

        # TODO: get_mem_topo can be enhanced by using real numa memory access latency

    return mem_topo


def cur_online_sockets() -> Set[int]:
    online_path: Path = _BASE_PATH / 'online'

    with online_path.open() as fp:
        line: str = fp.readline()
        sockets = convert_to_set(line)

    return sockets


def possible_sockets() -> Set[int]:
    possible_path: Path = _BASE_PATH / 'possible'

    with possible_path.open() as fp:
        line: str = fp.readline()
        sockets = convert_to_set(line)

    return sockets


def core_belongs_to(socket_id: int) -> Set[int]:
    cpulist_path: Path = _BASE_PATH / f'node{socket_id}/cpulist'

    with cpulist_path.open() as fp:
        line: str = fp.readline()
        return convert_to_set(line)


def _socket_to_core() -> Dict[int, Set[int]]:
    sockets = cur_online_sockets()
    return dict((socket_id, core_belongs_to(socket_id)) for socket_id in sockets)


def _core_to_socket() -> Dict[int, int]:
    ret_dict: Dict[int, int] = dict()
    sockets = cur_online_sockets()

    for socket_id in sockets:
        for core_id in core_belongs_to(socket_id):
            ret_dict[core_id] = socket_id

    return ret_dict


socket_to_core: Mapping[int, Set[int]] = _socket_to_core()  # key: socket id, value: corresponding core ids
core_to_socket: Mapping[int, int] = _core_to_socket()  # key: core id, value: corresponding socket id
