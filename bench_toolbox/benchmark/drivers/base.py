# coding: UTF-8

from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from itertools import chain
from signal import SIGCONT, SIGSTOP
from typing import ClassVar, Optional, Set, TYPE_CHECKING, Tuple

import psutil

if TYPE_CHECKING:
    from .engines.base import BaseEngine


class BenchDriver(metaclass=ABCMeta):
    """
    :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 가 무조건 이 클래스의 객체를 하나 변수로 가지며,
    그 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 가 벤치마크 실행을 명령받을 때, 어떻게 실행할 지를 담고있다.
    (:meth:`_launch_bench` 메소드)

    또한 벤치마크에 따라서 하나의 벤치마크를 실행하여도 여러 프로세스가 Process Tree를 이루며 실행되기도 하는데,
    이 때 어떤 프로세스가 실제로 연산을 하는 벤치마크이며, 그 프로세스의 PID가 무엇인지 찾아야 한다. (:meth:`_find_bench_proc` 메소드)
    """

    _benches: ClassVar[Set[str]]
    """
    :class:`Set` of benchmark names.

    All subclasses of :class:`BenchDriver` should override this variable with their own benchmark name.
    """

    _bench_home: ClassVar[str]
    """
    Base directory of the benchmark.

    All subclasses of :class:`BenchDriver` should override this variable with their own home directory.
    """

    bench_name: ClassVar[str]
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
        """
        `engine` 을 실행 엔진으로 하며, `num_threads` 개의 thread를 사용하는 `workload_name` 워크로드의 드라이버를 생성한다.

        :param name: 드라이버로 만들고자 하는 워크로드의 이름
        :type name: str
        :param num_threads: 워크로드가 사용할 thread 수
        :type num_threads: int
        :param engine: 만들어질 드라이버가 사용할 실행 엔진
        :type engine: bench_toolbox.benchmark.drivers.engines.base.BaseEngine
        :return: 드라이버 객체
        :rtype: bench_toolbox.benchmark.drivers.base.BenchDriver
        """
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
        .. TODO: change to class method

        Test that this driver can handle the benchmark `bench_name`.

        :param bench_name: benchmark name to test
        :type bench_name: str
        :return: ``True`` if this driver can handle
        :rtype: bool
        """
        pass

    @property
    def name(self) -> str:
        """
        :return: 워크로드 이름
        :rtype: str
        """
        return self._name

    @property
    def created_time(self) -> float:
        """
        :return: 프로세스가 시작한 시간
        :rtype: float
        """
        return self._bench_proc_info.create_time()

    @property
    def _is_running(self) -> bool:
        """
        Check if this benchmark is running.

        The difference with :meth:`BenchDriver.is_running` is this method is more precise,
        but has more cost.

        :return: ``True`` if running
        :rtype: bool
        """
        return self.is_running and self._find_bench_proc() is not None

    @property
    def has_invoked(self) -> bool:
        """
        :return: 한번이라도 실행된 적 있다면 ``True``
        :rtype: bool
        """
        return self._bench_proc_info is not None and \
               self._wrapper_proc is not None and \
               self._wrapper_proc_info is not None

    @property
    def is_running(self) -> bool:
        """
        :return: 워크로드가 실행되고 있다면 ``True``
        :rtype: bool
        """
        return self.has_invoked and self._bench_proc_info.is_running()

    @property
    def pid(self) -> Optional[int]:
        """
        Get effective pid of this benchmark (not python pid) without blocking.

        :return: actual pid of benchmark process
        :rtype: typing.Optional[int]
        """
        if self._bench_proc_info is None:
            return None
        else:
            return self._bench_proc_info.pid

    @abstractmethod
    async def _launch_bench(self) -> asyncio.subprocess.Process:
        """
        :attr:`_engine` 을 사용하여서 워크로드를 실행한다.

        내부적으로는 asyncio의 subprocess를 사용해야한다.

        :return: 실행 된 워크로드의 객체
        :rtype: asyncio.subprocess.Process
        """
        pass

    @abstractmethod
    def _find_bench_proc(self) -> Optional[psutil.Process]:
        """
        Try to find actual benchmark process (not a wrapper or a launcher of the benchmark set).

        This method will be periodically invoked until return value is not ``None``

        :return: ``None`` if the process not exists, :class:`psutil.Process` object if exists.
        :rtype: typing.Optional[psutil.Process]
        """
        pass

    async def run(self) -> None:
        """
        벤치마크를 실행한다.
        실행 명령을 내린 후 :meth:`_find_bench_proc` 를 통해 실제 벤치마크 프로세스의 시작이 될 때 까지 기다린다.

        .. todo::
            `asyncio.sleep` 대신 :keyword:`yield` 사용을 고려
        """
        self._bench_proc_info = None
        self._wrapper_proc = await self._launch_bench()
        self._wrapper_proc_info = psutil.Process(self._wrapper_proc.pid)

        while True:
            self._bench_proc_info = self._find_bench_proc()
            if self._bench_proc_info is not None:
                return
            await asyncio.sleep(0.1)

    async def join(self) -> None:
        """ 이 드라이버가 실행한 벤치마크가 종료될 때 까지 기다린다. """
        await self._wrapper_proc.wait()

    def stop(self) -> None:
        """ 이 드라이버가 실행한 벤치마크를 종료시킨다. """
        self._wrapper_proc.kill()
        self._bench_proc_info.kill()
        self._wrapper_proc_info.kill()

    def pause(self) -> None:
        """ 이 드라이버가 실행한 벤치마크를 잠시 멈춘다. """
        self._wrapper_proc.send_signal(SIGSTOP)
        self._bench_proc_info.suspend()

    def resume(self) -> None:
        """ 이 드라이버가 실행한 벤치마크를 다시 실행시킨다. """
        self._wrapper_proc.send_signal(SIGCONT)
        self._bench_proc_info.resume()

    def all_child_tid(self) -> Tuple[int, ...]:
        """
        이 드라이버로 실행된 벤치마크의 Process Tree안에 있는 모든 TID (Thread ID)를 반환한다.

        만약 실행중인 상태가 아니라면 빈 tuple을 반환한다.

        :return: 이 드라이버로 생성된 모든 Thread들의 TID
        :rtype: typing.Tuple[int, ...]
        """
        if self._bench_proc_info is None:
            return tuple()

        try:
            return tuple(chain(
                    (t.id for t in self._bench_proc_info.threads()),
                    *((t.id for t in proc.threads()) for proc in self._bench_proc_info.children(recursive=True))
            ))
        except psutil.NoSuchProcess:
            return tuple()
