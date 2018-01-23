# coding: UTF-8

import asyncio
import json
from abc import ABCMeta, abstractclassmethod
from typing import Optional, Set, Type

import psutil


class BenchDriver(metaclass=ABCMeta):
    _benches: Set[str] = None
    _bench_home: str = None
    bench_name: str = None

    def __init__(self, name: str, num_threads: int, binding_cores: str, numa_cores: Optional[str]):
        self._name: str = name
        self._num_threads: int = num_threads
        self._binging_cores: str = binding_cores
        self._numa_cores: Optional[str] = numa_cores

        self._bench_proc_info: Optional[psutil.Process] = None
        self._async_proc: Optional[asyncio.subprocess.Process] = None
        self._async_proc_info: Optional[psutil.Process] = None

    @staticmethod
    @abstractclassmethod
    def has(bench_name: str) -> bool:
        pass

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def get_bench_home(bench_name: str) -> str:
        from benchmark_launcher import GLOBAL_CFG_PATH
        with open(GLOBAL_CFG_PATH) as fp:
            return json.load(fp)['benchmark'][bench_name]

    @property
    def created_time(self) -> float:
        return self._bench_proc_info.create_time()

    @property
    def _is_running(self) -> bool:
        return self.is_running and self._find_bench_proc() is not None

    @property
    def is_running(self):
        return self._bench_proc_info is not None and \
               self._async_proc is not None and \
               self._async_proc_info is not None and \
               self._async_proc.returncode is None

    @property
    def pid(self) -> Optional[int]:
        """
        Get effective pid of this benchmark (not python pid) without blocking.
        :return: actual pid of benchmark process
        """
        if self._bench_proc_info is None:
            return None
        else:
            return self._bench_proc_info.pid

    @abstractclassmethod
    async def _launch_bench(self) -> asyncio.subprocess.Process:
        pass

    @abstractclassmethod
    def _find_bench_proc(self) -> Optional[psutil.Process]:
        pass

    async def run(self) -> None:
        self._async_proc = await self._launch_bench()
        self._async_proc_info = psutil.Process(self._async_proc.pid)

        while True:
            self._bench_proc_info = self._find_bench_proc()
            if self._bench_proc_info is not None:
                return
            await asyncio.sleep(0.1)

    async def join(self) -> None:
        if not self._is_running:
            raise RuntimeError(f'The benchmark ({self._name}) is already terminated or never invoked.'
                               ' Run benchmark first trough `run()`!')

        await self._async_proc.wait()

    def stop(self) -> None:
        self._async_proc.kill()
        try:
            self._bench_proc_info.kill()
            self._async_proc_info.kill()
        except psutil.NoSuchProcess:
            pass


def find_driver(workload_name) -> Type[BenchDriver]:
    from benchmark.driver.spec_driver import SpecDriver
    from benchmark.driver.parsec_driver import ParsecDriver
    from benchmark.driver.rodinia_driver import RodiniaDriver

    bench_drivers = (SpecDriver, ParsecDriver, RodiniaDriver)

    for _bench_driver in bench_drivers:
        if _bench_driver.has(workload_name):
            return _bench_driver

    raise ValueError(f'Can not find appropriate driver for workload : {workload_name}')


def bench_driver(workload_name: str, num_threads: int, binding_cores: str, numa_cores: Optional[str]) -> BenchDriver:
    _bench_driver = find_driver(workload_name)

    return _bench_driver(workload_name, num_threads, binding_cores, numa_cores)
