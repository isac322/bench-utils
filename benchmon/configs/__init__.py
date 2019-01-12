# coding: UTF-8

import json
from collections import Mapping
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Tuple

from ..benchmark.drivers import bench_drivers


def get_full_path(config_file_name: str) -> Path:
    with resources.path(__package__, config_file_name) as path:
        return path


_cached_config_map: Dict[Path, Tuple[Dict[str, Any], int]] = dict()


# FIXME: additional validation of config.json ('default_wl_parser')
def validate_and_load(config_path: Path) -> Dict[str, Any]:
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
    config: Mapping[str, str] = validate_and_load(get_full_path('benchmark_home.json'))

    for _bench_driver in bench_drivers:
        _bench_driver._bench_home = config[_bench_driver.bench_name]


_parse_bench_home()
