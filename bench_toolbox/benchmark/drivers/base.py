# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from itertools import chain
from signal import SIGCONT, SIGSTOP
from typing import ClassVar, Optional, Set, TYPE_CHECKING, Tuple

import psutil

from ..decorators.driver import ensure_invoked, ensure_not_running, ensure_running

if TYPE_CHECKING:
    from .engines.base import BaseEngine


class BenchDriver(metaclass=ABCMeta):
    _benches: ClassVar[Set[str]] = None
    """
    :class:`Set` of benchmark names.
    
    All subclasses of :class:`BenchDriver` should override this variable with their own benchmark name.
    """

    _bench_home: ClassVar[str] = None
    """
    Base directory of the benchmark.
    
    All subclasses of :class:`BenchDriver` should override this variable with their own home directory.
    """

    bench_name: ClassVar[str] = None
    """
    Benchmark set name.
    
    All subclasses of :class:`BenchDriver` should override this variable with their own benchmark set name.
    """

    _name: str
    _num_threads: int
    _engine: BaseEngine
    _bench_proc_info: Optional[psutil.Process] = None
    _wrapper_proc: Optional[asyncio.subprocess.Process] = None
    _wrapper_proc_info: Optional[psutil.Process] = None

    def __init__(self, name: str, num_threads: int, engine: BaseEngine):
        self._name = name
        self._num_threads = num_threads
        self._engine = engine

    def __del__(self):
        if self._is_running:
            try:
                self.stop()
            except (psutil.NoSuchProcess, ProcessLookupError):
                pass

    @staticmethod
    @abstractmethod
    def has(bench_name: str) -> bool:
        """
        Test that this driver can handle the benchmark *bench_name*.

        :param bench_name: benchmark name to test
        :return: ``True`` if this driver can handle
        """
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    @ensure_invoked
    def created_time(self) -> float:
        return self._bench_proc_info.create_time()

    @property
    def _is_running(self) -> bool:
        """
        Check if this benchmark is running.

        The difference with :meth:`BenchDriver.is_running` is this method is more precise,
        but has more cost.

        :return: ``True`` if running
        """
        return self.is_running and self._find_bench_proc() is not None

    @property
    def has_invoked(self) -> bool:
        return self._bench_proc_info is not None and \
               self._wrapper_proc is not None and \
               self._wrapper_proc_info is not None

    @property
    def is_running(self) -> bool:
        return self.has_invoked and self._bench_proc_info.is_running()

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

    @abstractmethod
    async def _launch_bench(self) -> asyncio.subprocess.Process:
        pass

    @abstractmethod
    def _find_bench_proc(self) -> Optional[psutil.Process]:
        """
        Try to find actual benchmark process (not a wrapper or a launcher of the benchmark set).

        This method will be periodically invoked until return value is not ``None``

        :return: ``None`` if the process not exists, :class:`psutil.Process` object if exists.
        """
        pass

    @ensure_not_running
    async def run(self) -> None:
        self._bench_proc_info = None
        self._wrapper_proc = await self._launch_bench()
        self._wrapper_proc_info = psutil.Process(self._wrapper_proc.pid)

        while True:
            self._bench_proc_info = self._find_bench_proc()
            if self._bench_proc_info is not None:
                return
            await asyncio.sleep(0.1)

    @ensure_running
    async def join(self) -> None:
        await self._wrapper_proc.wait()

    def stop(self) -> None:
        self._wrapper_proc.kill()
        self._bench_proc_info.kill()
        self._wrapper_proc_info.kill()

    @ensure_running
    def pause(self) -> None:
        self._wrapper_proc.send_signal(SIGSTOP)
        self._bench_proc_info.suspend()

    @ensure_running
    def resume(self) -> None:
        self._wrapper_proc.send_signal(SIGCONT)
        self._bench_proc_info.resume()

    @ensure_running
    def all_child_tid(self) -> Tuple[int, ...]:
        if self._bench_proc_info is None:
            return tuple()

        try:
            return tuple(chain(
                    (t.id for t in self._bench_proc_info.threads()),
                    *((t.id for t in proc.threads()) for proc in self._bench_proc_info.children(recursive=True))
            ))
        except psutil.NoSuchProcess:
            return tuple()
