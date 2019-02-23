# coding: UTF-8

"""
:mod:`drivers` -- :class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>` 별로 실제 실행하려고 할 때, 어떤 커맨드로 실행해야하는지 서술
=========================================================================================================================================

:class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>` 마다 필수적으로 하나씩 포함되며,
벤치마크를 실행하려고 할 때 어떻게 실행 해야할지를 담당한다.
(:meth:`benchmon.benchmark.drivers.base.BenchDriver._launch_bench` 참조)

또한 벤치마크마다 여러 프로세스가 생성되기도하며, Process Tree의 형태가 달라서 어떤 프로세스의 PID를 모니터링 해야하는지도 달라지는데,
드라이버가 벤치마크별로 어떤 프로세스를 모니터링 해야하는지도 찾아줘야한다.
(:meth:`benchmon.benchmark.drivers.base.BenchDriver._find_bench_proc` 참조)

예를 들어 `PARSEC` 은 `parsecmgmt` 커맨드를 통해 실행되며, `SPEC CPU` 는 `runspec` 를 통해 실행되는데,
`PARSEC` 과 `SPEC` 의 드라이버에는 그 커맨드들을 사용하여 벤치마크를 실행하도록 기술한다.

새로운 종류의 벤치마크를 사용하려면 :class:`~benchmon.benchmark.drivers.base.BenchDriver` 를 상속받는 새로운 드라이버를 작성해야한다.

.. seealso::

    :mod:`benchmon.benchmark.drivers.engines` 모듈
        사실 드라이버 혼자만으로는 실행될 수 없고, 드라이버에 서술된 커맨드를 어떻게 실행할지 서술

.. module:: benchmon.benchmark.drivers
    :synopsis: 벤치마크마다 실제 실행과 관련된 정보를 서술
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from typing import Tuple, Type

from .base import BenchDriver
from .engines.base import BaseEngine
from .npb import NPBDriver
from .parsec import ParsecDriver
from .rodinia import RodiniaDriver
from .spec import SpecDriver

# TODO: adds drivers dynamically
bench_drivers: Tuple[Type[BenchDriver], ...] = (SpecDriver, ParsecDriver, RodiniaDriver, NPBDriver)
"""
사용가능한 모든 드라이버들. 이 목록안에 있는 드라이버들은 :func:`find_driver` 를 통해 워크로드 이름만으로 드라이버를 찾을 수 있다.
"""


def find_driver(workload_name: str) -> Type[BenchDriver]:
    """
    `workload_name` 를 다루는 드라이버를 찾아준다.

    .. note::

        * 드라이버가 :data:`bench_drivers` 에 포함 되어있어야 찾을 수 있다.
        * 여러 드라이버가 `workload_name` 을 다룰 수 있다면, 먼저 추가된 드라이버를 우선한다.

    :param workload_name: 찾고자하는 워크로드의 이름
    :type workload_name: str
    :return: `workload_name` 를 다룰 수 있는 드라이버
    :rtype: typing.Type[benchmon.benchmark.drivers.base.BenchDriver]
    :raise ValueError: 드라이버를 찾을 수 없을 때
    """
    for _bench_driver in bench_drivers:
        if _bench_driver.has(workload_name):
            return _bench_driver

    raise ValueError(f'Can not find appropriate driver for workload : {workload_name}')


def gen_driver(workload_name: str, num_threads: int, engine: BaseEngine) -> BenchDriver:
    """
    `engine` 을 실행 엔진으로 하며, `num_threads` 개의 thread를 사용하는 `workload_name` 워크로드의 드라이버를 생성한다.

    :param workload_name: 드라이버로 만들고자 하는 워크로드의 이름
    :type workload_name: str
    :param num_threads: 워크로드가 사용할 thread 수
    :type num_threads: int
    :param engine: 만들어질 드라이버가 사용할 실행 엔진
    :type engine: benchmon.benchmark.drivers.engines.base.BaseEngine
    :return: 드라이버 객체
    :rtype: benchmon.benchmark.drivers.base.BenchDriver
    :raise ValueError: 드라이버를 찾을 수 없을 때
    """
    _bench_driver = find_driver(workload_name)

    return _bench_driver(workload_name, num_threads, engine)
