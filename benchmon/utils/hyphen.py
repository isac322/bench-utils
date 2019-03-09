# coding: UTF-8

"""
:mod:`hyphen` -- cgroup이나 resctrl에서 사용하는 `-` 이 포함된 문자열 처리
==========================================================================

`0,2-4` 와 같은 문자열을 처리하기 위한 모듈

.. module:: benchmon.utils.hyphen
    :synopsis: cgroup이나 resctrl에서 사용하는 - 이 포함된 문자열 처리
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from typing import Iterable, Set


def convert_to_set(hyphen_str: str) -> Set[int]:
    """
    hyphen string을 읽어서 `Set[int]` 로 변환한다

    :param hyphen_str: 변환할 hyphen string
    :type hyphen_str: str
    :return: 변환된 정수들의 집합
    :rtype: typing.Set[int]
    """
    ret = set()

    for elem in hyphen_str.split(','):
        group = tuple(map(int, elem.split('-')))

        if len(group) is 1:
            ret.add(group[0])
        elif len(group) is 2:
            ret.update(range(group[0], group[1] + 1))

    return ret


def convert_to_hyphen(core_ids: Iterable[int]) -> str:
    """
    정수들을 hyphen string으로 변환한다

    .. todo::
        valid한 hyphen string이지만 minimal하진 않은 결과를 반환하다

    :param core_ids: hyphen string으로 변환할 정수들
    :type core_ids: typing.Iterable[int]
    :return: 변환된 hyphen string
    :rtype: str
    """
    return ','.join(map(str, set(core_ids)))
