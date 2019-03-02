# coding: UTF-8

from dataclasses import dataclass
from types import ModuleType
from typing import Tuple

from benchmon.configs.containers import BaseConfig


@dataclass(frozen=True)
class LauncherConfig(BaseConfig):
    post_scripts: Tuple[ModuleType, ...]
    hyper_threading: bool
    stops_with_the_first: bool
