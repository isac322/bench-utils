# coding: UTF-8

"""
:mod:`ranges` -- cgroup이나 resctrl에서 사용하는 `-` 이 포함된 문자열 처리
==========================================================================

`0,2-4` 와 같은 문자열을 처리하기 위한 모듈

.. module:: benchmon.utils.ranges
    :synopsis: resctrl 등에서 사용하는 - 이 포함된 문자열 처리
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, Collection, Iterable, Iterator, Pattern, Set, Tuple


class Ranges(Collection[int]):
    __slots__ = ('_range',)

    _RANGE_PATTERN: ClassVar[Pattern[str]] = re.compile(r'^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$')
    _range: Set[int]

    def __init__(self, initial_range: Iterable[int]) -> None:
        self._range = set(initial_range)

    def __iter__(self) -> Iterator[int]:
        return self._range.__iter__()

    def __contains__(self, item: Any) -> bool:
        return item in self._range

    def __len__(self) -> int:
        return len(self._range)

    @classmethod
    def _validate(cls, feed: str) -> bool:
        return cls._RANGE_PATTERN.match(feed) is not None

    @classmethod
    def parse(cls, feed: str) -> Ranges:
        """
        hyphen string을 읽어서 `Set[int]` 로 변환한다

        :param feed: 변환할 hyphen string
        :type feed: str
        """
        if not cls._validate(feed):
            raise ValueError(f'`{feed}` is not a valid range string.')

        ret = set()

        for elem in feed.split(','):
            group = tuple(map(int, elem.split('-')))

            if len(group) is 1:
                ret.add(group[0])
            elif len(group) is 2:
                ret.update(range(group[0], group[1] + 1))

        return cls(ret)

    @classmethod
    def from_str(cls, feed: str) -> Ranges:
        return cls.parse(feed)

    @classmethod
    def from_iterable(cls, iterable: Iterable[int]) -> Ranges:
        return cls(iterable)

    @classmethod
    def convert_to_str(cls, iterable: Iterable[int]) -> str:
        return cls(iterable).to_str()

    def to_set(self) -> Set[int]:
        return self._range.copy()

    def to_str(self) -> str:
        """
        정수들을 hyphen string으로 변환한다

        .. todo::
            valid한 hyphen string이지만 minimal하진 않은 결과를 반환하다

        :return: 변환된 hyphen string
        :rtype: str
        """
        return ','.join(map(str, self._range))

    def to_tuple(self) -> Tuple[int, ...]:
        return tuple(self._range)
