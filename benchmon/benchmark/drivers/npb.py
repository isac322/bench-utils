# coding: UTF-8

import asyncio
from typing import ClassVar, Dict, Optional, Set

import psutil

from .base import BenchDriver


class NPBDriver(BenchDriver):
    """ NPB 벤치마크의 실행을 담당하는 드라이버 """

    _benches: ClassVar[Set[str]] = {'CG', 'IS', 'DC', 'EP', 'MG', 'FT', 'SP', 'BT', 'LU', 'UA'}
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

    @classmethod
    def has(cls, bench_name: str) -> bool:
        return bench_name in NPBDriver._benches

    def _find_bench_proc(self) -> Optional[psutil.Process]:
        if self._wrapper_proc_info.name() == self._exec_name and self._wrapper_proc_info.is_running():
            return self._wrapper_proc_info

        return None

    async def _launch_bench(self) -> asyncio.subprocess.Process:
        return await self._engine.launch(f'{self._bench_home}/bin/{self._exec_name}',
                                         stdout=asyncio.subprocess.DEVNULL,
                                         env={'OMP_NUM_THREADS': str(self._num_threads)})
