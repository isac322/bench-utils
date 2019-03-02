# coding: UTF-8

import importlib
from pathlib import Path
from types import ModuleType
from typing import Tuple

from benchmon.configs.parsers import LocalReadParser
from ..containers.launcher import LauncherConfig


class LauncherParser(LocalReadParser[LauncherConfig]):
    """
    `config.json` 에 포함된 `launcher` 를 키로 하는 설정값들을 파싱하는 클래스.
    """

    @classmethod
    def _get_path(cls, script_name: str) -> ModuleType:
        return importlib.import_module(f'hybrid_iso.post_scripts.{Path(script_name).stem}')

    def _parse(self) -> LauncherConfig:
        config = self._local_config['launcher']

        post_scripts: Tuple[ModuleType, ...] = tuple(map(self._get_path, config.get('post_scripts', tuple())))
        stops_with_the_first: bool = config.get('stops_with_the_first', False)
        hyper_threading: bool = config.get('hyper-threading', False)

        return LauncherConfig(post_scripts, hyper_threading, stops_with_the_first)
