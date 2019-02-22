# coding: UTF-8

"""
:mod:`benchmark` -- benchmark 종류별로 benchmark를 파싱하는 파서들 모음
=======================================================================

설정파일의 내용을 입력으로 주면, :class:`~benchmon.benchmark.base.BaseBenchmark` 객체를 생성하는 파서들을 가지고있다.
하지만, :class:`~benchmon.benchmark.base.BaseBenchmark` 의 여러 자식 클래스들이 있을 수 있으며,
각 벤치마크마다 설정파일의 내용이 달라 서로 파싱방법이 상이할 수 있다.
따라서 벤치마크 종류별로 :class:`~benchmon.configs.parsers.benchmark.base.BaseBenchParser` 를 부모로하는 파서를 따로 구현하고,
설정파일의 내용에 맞는 파서를 불러와 파싱한다.

파서의 종류는 문자열로 표시하며, 설정파일 내에 전역으로 `default_wl_parser` 혹은 각 workload 별로 `parser` 를 key로하는 곳에 파서의
종류를 표시해야한다.

.. note::

    * :class:`~benchmon.configs.parsers.benchmark.base.BaseBenchParser` 를 부모로하는 파서는 `_PARSABLE_TYPES`
      클래스 변수를 꼭 override 해야하며, :func:`~benchmon.configs.parsers.benchmark.base.BaseBenchParser.register_parser`
      를 통해 클래스 자신을 등록해야지만 설정파일을 파싱할 때 benchmon에서 자동으로 그 파서를 찾을 수 있다.

.. seealso::

    * `hybrid_iso/config.template.json`: 파서 표시의 예시

.. module:: benchmon.configs.parsers.benchmark
    :synopsis: 종류별로 benchmark를 파싱하는 파서들 모음
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseBenchParser
from .launchable import LaunchableParser

BaseBenchParser.register_parser(LaunchableParser)
