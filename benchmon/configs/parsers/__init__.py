# coding: UTF-8

"""
:mod:`parsers` -- 각종 설정파일을 읽어들이는 파서들
=========================================================

다양한 설정파일을 읽어서 파싱하여 주로 :mod:`~benchmon.configs.containers` 의 컨테이너를 생성한다.

외부 설정파일가 필요한 파서, 필요없는 파서 혹은 특정 설정 (e.g. perf, RabbitMQ)을 읽어들이는 파서 등 특성에 따라 여러 파서로 나뉨

.. module:: benchmon.configs.parsers
    :synopsis: JSON 형태의 설정을 읽는 파서
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

from .base import BaseParser, LocalReadParser
from .bench import BenchParser
from .perf import PerfParser
from .rabbit_mq import RabbitMQParser
