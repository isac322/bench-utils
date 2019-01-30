# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Dict, TYPE_CHECKING, Tuple, Type

from .base import BaseConstraint
from .base_builder import BaseBuilder
from ...utils.dvfs import read_max_freqs, set_max_freq, set_max_freqs

if TYPE_CHECKING:
    from ..base import BaseBenchmark


class DVFSConstraint(BaseConstraint):
    """
    :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 의 실행전에 특정 코어들의 CPU frequency를
    입력받은 값으로 설정하며, 벤치마크의 실행이 종료될 경우 그 코어들의 CPU frequency를 원래대로 복구시킨다.
    """
    _target_freq: int
    _core_ids: Tuple[int, ...]
    _orig_freq: Dict[int, int]

    def __new__(cls: Type[DVFSConstraint], bench: BaseBenchmark,
                core_ids: Tuple[int, ...], freq: int) -> DVFSConstraint:
        """
        .. TODO: `core_ids` 의 타입을 Iterable로 변경
        :param bench: 이 constraint가 붙여질 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>`
        :type bench: bench_toolbox.benchmark.base.BaseBenchmark
        :param core_ids: frequency를 조절 할 CPU 코어 ID들
        :type core_ids: typing.Tuple[int, ...]
        :param freq: 변경할 frequency 값
        :type freq: int
        """
        obj: DVFSConstraint = super().__new__(cls, bench)

        obj._core_ids = core_ids
        obj._target_freq = freq
        obj._orig_freq = dict()

        return obj

    async def on_init(self) -> None:
        orig_freq = await read_max_freqs(self._core_ids)
        self._orig_freq = dict(zip(self._core_ids, orig_freq))

    async def on_start(self) -> None:
        await set_max_freqs(self._core_ids, self._target_freq)

    async def on_destroy(self) -> None:
        await asyncio.wait(tuple(
                set_max_freq(core_id, freq)
                for core_id, freq in self._orig_freq.items()
        ))

    class Builder(BaseBuilder['DVFSConstraint']):
        """ :class:`~bench_toolbox.benchmark.constraints.dvfs.DVFSConstraint` 를 객체화하는 빌더 """
        _core_ids: Tuple[int, ...]
        _target_freq: int

        def __init__(self, core_ids: Tuple[int, ...], freq: int) -> None:
            """
            .. TODO: `core_ids` 의 타입을 Iterable로 변경
            :param core_ids: frequency를 조절 할 CPU 코어 ID들
            :type core_ids: typing.Tuple[int, ...]
            :param freq: 변경할 frequency 값
            :type freq: int
            """
            super().__init__()

            self._core_ids = core_ids
            self._target_freq = freq

        def finalize(self, benchmark: BaseBenchmark) -> DVFSConstraint:
            return DVFSConstraint.__new__(DVFSConstraint, benchmark, self._core_ids, self._target_freq)
