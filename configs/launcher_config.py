# coding: UTF-8

from pathlib import Path
from typing import List, Tuple


class LauncherConfig:
    def __init__(self, post_script: List[Path], hyper_threading: bool, stops_with_the_first: bool):
        self._post_scripts: Tuple[Path] = tuple(post_script)
        self._hyper_threading: bool = hyper_threading
        self._stops_with_the_first: bool = stops_with_the_first

    @property
    def post_scripts(self) -> Tuple[Path]:
        return self._post_scripts

    @property
    def hyper_threading(self) -> bool:
        return self._hyper_threading

    @property
    def stops_with_the_first(self) -> bool:
        return self._stops_with_the_first
