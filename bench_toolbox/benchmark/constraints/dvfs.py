# coding: UTF-8

from __future__ import annotations

import asyncio
from typing import Dict, Tuple, Type

from .base import BaseConstraint
from .base_builder import BaseBuilder
from ..base import BaseBenchmark
from ...utils.dvfs import read_max_freqs, set_max_freq, set_max_freqs


class DVFSConstraint(BaseConstraint):
    _target_freq: int
    _core_ids: Tuple[int, ...]
    _orig_freq: Dict[int, int]

    def __new__(cls: Type[DVFSConstraint], bench: BaseBenchmark,
                core_ids: Tuple[int, ...], freq: int) -> DVFSConstraint:
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
        _core_ids: Tuple[int, ...]
        _target_freq: int

        def __init__(self, core_ids: Tuple[int, ...], freq: int) -> None:
            super().__init__()

            self._core_ids = core_ids
            self._target_freq = freq

        def finalize(self, benchmark: BaseBenchmark) -> DVFSConstraint:
            return DVFSConstraint.__new__(DVFSConstraint, benchmark, self._core_ids, self._target_freq)
