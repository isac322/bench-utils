# coding: UTF-8

import asyncio
from typing import ClassVar, Dict, FrozenSet, Optional

import psutil

from .base import BenchDriver
from .engines.base import BaseEngine
from ... import Context
from ...benchmark import BaseBenchmark


class NPBDriver(BenchDriver):
    """ NPB 벤치마크의 실행을 담당하는 드라이버 """

    _benches: ClassVar[FrozenSet[str]] = frozenset(('CG', 'IS', 'DC', 'EP', 'MG', 'FT', 'SP', 'BT', 'LU', 'UA'))
    bench_name: ClassVar[str] = 'npb'

    # TODO: variable data size
    DATA_SET_MAP: ClassVar[Dict[str, str]] = {
        'CG': 'C',
        'IS': 'D',
        'DC': 'B',
        'EP': 'C',
        'MG': 'C',
        'FT': 'C',
        'SP': 'C',
        'BT': 'C',
        'LU': 'C',
        'UA': 'C',
    }

    @property
    def _exec_name(self) -> str:
        """
        미리 정의 된 Data Set에 따라서 실제 executable binary의 이름을 결정한다.

        :return: executable binary name
        :rtype: str
        """
        return f'{self._name.lower()}.{NPBDriver.DATA_SET_MAP[self._name]}.x'

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._wrapper_proc_info.name() == self._exec_name and self._wrapper_proc_info.is_running():
            return self._wrapper_proc_info

        return None

    async def _launch_bench(self, context: Context) -> asyncio.subprocess.Process:
        engine = BaseEngine.of(context)
        config = BaseBenchmark.of(context).bench_config

        return await engine.launch(
                context,
                f'{self._bench_home}/bin/{self._exec_name}',
                stdout=asyncio.subprocess.DEVNULL,
                env={'OMP_NUM_THREADS': str(config.num_of_threads)}
        )
