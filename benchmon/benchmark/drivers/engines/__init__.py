# coding: UTF-8

"""
:mod:`engines` -- :class:`드라이버 <benchmon.benchmark.drivers.base.BenchDriver>` 가 벤치마크를 실행할 방법을 서술
========================================================================================================================

:class:`~benchmon.benchmark.drivers.base.BenchDriver` 가 벤치마크를 실행할 때,
자원 제한을 위해 `numactl` 이나 `cgroup` 을 사용하는데, 이러한 프로그램들은 벤치마크 명령줄을 argument로 받는다.
(e.g. `numactl --localalloc ls -al /`, `cgexec -g cpuset:test ls -al /`)
그 부분을 모듈화 하기위하여 :mod:`engines` 이 있으며, :class:`드라이버 <benchmon.benchmark.drivers.base.BenchDriver>` 는
무조건 한 :class:`엔진 <benchmon.benchmark.drivers.engines.base.BaseEngine>` 을 attribute로 가져서 벤치마크 실행 시 사용해야한다.

.. note::

    아직 구조가 정확하게 잡힌 패키지와 클래스들이 아님

.. todo::

    * local config.json을 보고 유추하거나, 설정할 수 있는 기능 추가
    * context pattern을 사용한다면 그냥 드라이버에 통합 될수도?

.. seealso::

    :mod:`benchmon.benchmark.drivers` 모듈
        모든 엔진은 드라이버에서 사용된다.

.. module:: benchmon.benchmark.drivers.engines
    :synopsis: 벤치마크 드라이버의 실행 커맨드가 실행될 방법을 서술
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .cgroup import CGroupEngine
from .numactl import NumaCtlEngine
