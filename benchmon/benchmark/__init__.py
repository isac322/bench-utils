# coding: UTF-8

"""
:mod:`benchmark` -- 벤치마크를 실행시키는 방법, 벤치마크의 종류, 자원 제약 등 벤치마크의 실행과 관련된 클래스 모음
=========================================================================================================

* 벤치마크를 실제로 실행하는 클래스들: :mod:`benchmon.benchmark.drivers`

* 벤치마크를 실행할 때 실행 커맨드를 정의하는 클래스들: :mod:`benchmon.benchmark.drivers.engines`

* 벤치마크의 실행 전후로 자원 할당, 해제 등 제약 사항을 정의하는 클래스들: :mod:`benchmon.benchmark.constraints`

* 가장 high-level에서 벤치마크를 실행하고 모니터링하는 클래스들: :mod:`benchmon.benchmarks`


**이 문서에서 설명하는 부분은 맨 마지막 클래스들에대한 설명이다** (다른 모듈둘의 설명은 해당 모듈 페이지에 상세하게 적혀있다.)



벤치마크의 실행과 종료, 일시 정지, 모니터링 등을 담당하는 high-level 클래스는 :class:`benchmon.benchmark.base.BaseBenchmark` 이다.
벤치마크의 실행과 종료에 해당하는 부분만 low-level로 :mod:`benchmon.benchmark.drivers` 에 있는 클래스들을 사용할 수 있지만,
코드의 유지보수 입장에서 권장하지 않는다.

따라서 벤치마크 프로세스를 처음부터 실행하고 모니터링 하는 경우 (e.g. NPB, PARSEC 등)는
:class:`~benchmon.benchmark.base.BaseBenchmark` 를 상속 받아 이미 구현 된
:class:`~benchmon.benchmark.launchable.LaunchableBenchmark` 를 사용하면 된다.

벤치마크 프로세스는 이미 실행 되어있고, 부하를 주는 프로그램을 실행해야하는 경우 (e.g. 웹 서버와 request generator)는
:class:`~benchmon.benchmark.launchable.LaunchableBenchmark` 를 사용할 수 없고,
:class:`~benchmon.benchmark.base.BaseBenchmark` 를 상속 받아 새로운 Benchmark 클래스를 작성해야한다.

그 외에도 이미 구현된 각각의 벤치마크 클래스들의 목적에 부합하지 않은 다른 벤치마크를 실행해야 할 경우,
새로 구현하는것이 유지보수면에서 바람직하다.


**모든 벤치마크 클래스들은 생성자를 통해 바로 객체화할 수 없도록 되어있으며, 새로 구현되는 클래스 또한 그래야한다.**

`Build Pattern <https://johngrib.github.io/wiki/builder-pattern/>`_ 이 적용되어있기 때문에,
생성자 대신 각 클래스에 매칭되는 빌더를 사용해야한다.

기본 빌더는 :class:`~benchmon.benchmark.base_builder.BaseBuilder` 이며,
:class:`benchmon.benchmark.launchable.LaunchableBenchmark` 의 빌더는
:class:`benchmon.benchmark.launchable.LaunchableBenchmark.Builder` 이다.

빌더의 자세한 사용법은 :class:`~benchmon.benchmark.base_builder.BaseBuilder` 에서 볼 수 있다.



.. module:: benchmon.benchmark
    :synopsis: 벤치마크의 실행과 관련된 클래스 모음
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseBenchmark
from .base_builder import BaseBuilder
from .launchable import LaunchableBenchmark

BaseBenchmark.register_nickname(LaunchableBenchmark)
