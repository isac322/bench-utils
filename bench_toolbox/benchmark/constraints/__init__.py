# coding: UTF-8

"""
:mod:`constraints` -- :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 가 실행되기 전에 선행 되어야 할 조건들
========================================================================================================================

.. TODO: life cycle 설명 혹은 링크

:class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 가 실행되기 전에 갖춰야 하는 조건과 종료된 후의 처리를 기술한다.

예를 들어 해당 벤치마크가 어떤 cgroup에 속할지, 그 그룹의 설정값들은 어때야 하는지,
또한 그 벤치마크가 종료 되었을 경우 해당 cgroup을 어떻게 처리할 것인지 등,
벤치마크가 실행되기 전에 갖춰져야하는 조건을 설정하며 그와함께 종료된 후의 처리를 설정한다.

.. note::

    * DVFS, resctrl, cgroup 등은 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 생성 시,
      local config.json의 내용을 보고 자동으로 생성한다.
    * 모든 constraint 클래스들은 직접 객체화하지 않고, 각 클래스에 알맞는
      :class:`빌더 <bench_toolbox.benchmark.constraints.base_builder.BaseBuilder>` 를 통해 객체화한다.

.. module:: bench_toolbox.benchmark.constraints
    :synopsis: 벤치마크 실행 전후의 환경 설정
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseConstraint
from .base_builder import BaseBuilder
from .dvfs import DVFSConstraint
from .resctrl import ResCtrlConstraint
