# coding: UTF-8

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, Generic, Mapping, Optional, TypeVar

from .. import validate_and_load

T = TypeVar('T')


class BaseParser(Generic[T], metaclass=ABCMeta):
    _cached: Optional[T]

    def __init__(self) -> None:
        self._cached = None

    @abstractmethod
    def _parse(self) -> T:
        pass

    def parse(self) -> T:
        if self._cached is None:
            self._cached = self._parse()

        return self._cached

    def is_cached(self) -> bool:
        return self._cached is not None


class LocalReadParser(BaseParser[T], ABC):
    _local_config: Mapping[str, Any]
    _workspace: Path

    def __init__(self, workspace: Path) -> None:
        super().__init__()

        self._local_config = validate_and_load(workspace / 'config.json')
        self._workspace = workspace

    def reload_local_cfg(self) -> LocalReadParser:
        self._local_config = validate_and_load(self._workspace / 'config.json')
        self._cached = None
        return self
