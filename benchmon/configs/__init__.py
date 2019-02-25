# coding: UTF-8

"""
:mod:`configs` -- JSON 조작으로 가능한 설정 파일들을 파싱
=========================================================

:class:`벤치마크 <benchmon.benchmark.base.BaseBenchmark>` 객체를 생성할 때 필요한 벤치마크 설정이나 perf나 RabbitMQ를
설정하는 JSON파일을 읽어서 파싱하는 모듈.

:mod:`~benchmon.configs.parsers` 의 파서들이 파싱하여 :mod:`~benchmon.configs.containers` 의 컨테이너를 생성한다.

설정파일은 JSON형태로 작성해야하며, 되도록 레포지토리에 직접 추가하지 않고 템플릿으로 놔둔다.

.. todo::

    * 파싱할 때 검증도 하면 좋을 듯

.. module:: benchmon.configs
    :synopsis: 각종 설정파일들을 파싱
.. moduleauthor:: Byeonghoon Yoo <bh322yoo@gmail.com>
"""

import json
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from ..benchmark.drivers import BenchDriver


def get_full_path(config_file_name: str) -> Path:
    """
    읽고싶은 설정파일의 이름을 주면, 파일 읽기를 위한 :class:`~pathlib.Path` 객체로 반환.

    :param config_file_name: 읽고싶은 설정파일의 이름
    :type config_file_name: str
    :return: 설정파일의 경로 객체
    :rtype: pathlib.Path
    """
    with resources.path(__package__, config_file_name) as path:
        return path


_cached_config_map: Dict[Path, Tuple[Dict[str, Any], int]] = dict()


# FIXME: additional validation of config.json ('default_wl_parser')
def validate_and_load(config_path: Path) -> Dict[str, Any]:
    """
    JSON 설정파일의 경로를 통해 파일을 읽어 내용을 반환한다.

    .. note::
        * 함수 이름에는 validate이 있지만 여기서 validate이란, 존재하는 파일인지, 읽을 수 JSON파일인지만 체크한다.
          내용에대한 validation은 각 파서 내부에서 진행해야한다.

    :raises FileNotFoundError: 해당 경로에 파일이 없을 경우

    :param config_path: 읽고싶은 파일의 경로
    :type config_path: pathlib.Path
    :return: JSON 설정파일의 내용
    :rtype: typing.Dict[str, typing.Any]
    """
    if not config_path.is_file():
        raise FileNotFoundError(
                f'\'{config_path.absolute()}\' does not exist. Please copy a template and modify it')

    current_mtime = config_path.stat().st_mtime

    if config_path in _cached_config_map \
            and current_mtime <= _cached_config_map[config_path][1]:
        return _cached_config_map[config_path][0]

    else:
        with config_path.open() as fp:
            content = json.load(fp)
            _cached_config_map[config_path] = (content, current_mtime)
            return content


# FIXME: 다른 방법은 없나?
def _parse_bench_home() -> None:
    """
    :mod:`benchmon.benchmark.drivers` 에 등록된 모든 :class:`드라이버 <benchmon.benchmark.drivers.baseBenchDriver>` 에 대해서
    각 드라이버가 실행하는 벤치마크의 경로를 `benchmark_home.json` 로부터 읽어 입력한다.
    """
    config: Mapping[str, str] = validate_and_load(get_full_path('benchmark_home.json'))

    for _bench_driver in BenchDriver._registered_drivers:
        _bench_driver._bench_home = config[_bench_driver.bench_name]


_parse_bench_home()
