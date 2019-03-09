# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Dict, Iterable, TYPE_CHECKING, Tuple

from .base import BaseConstraint
from ...utils.dvfs import read_max_freqs, set_max_freq, set_max_freqs

if TYPE_CHECKING:
    from ... import Context


class DVFSConstraint(BaseConstraint):
    """
    :class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>` 의 실행전에 특정 코어들의 CPU frequency를
    입력받은 값으로 설정하며, 벤치마크의 실행이 종료될 경우 그 코어들의 CPU frequency를 원래대로 복구시킨다.
    """
    _target_freq: int
    _core_ids: Tuple[int, ...]
    _orig_freq: Dict[int, int]

    def __init__(self, core_ids: Iterable[int], freq: int) -> None:
        """
        :param core_ids: frequency를 조절 할 CPU 코어 ID들
        :type core_ids: typing.Iterable[int]
        :param freq: 변경할 frequency 값
        :type freq: int
        """
        self._core_ids = tuple(core_ids)
        self._target_freq = freq
        self._orig_freq = dict()

    async def on_init(self, context: Context) -> None:
        orig_freq = await read_max_freqs(self._core_ids)
        self._orig_freq = dict(zip(self._core_ids, orig_freq))

    async def on_start(self, context: Context) -> None:
        await set_max_freqs(self._core_ids, self._target_freq)

    async def on_destroy(self, context: Context) -> None:
        await asyncio.wait(tuple(
                set_max_freq(core_id, freq)
                for core_id, freq in self._orig_freq.items()
        ))
