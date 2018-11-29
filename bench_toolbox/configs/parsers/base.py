# coding: UTF-8

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Generic, Mapping, Optional, TypeVar

T = TypeVar('T')


class BaseParser(Generic[T], metaclass=ABCMeta):
    _name: ClassVar[str]
    _cached: Optional[T]

    def __init__(self) -> None:
        self._cached = None

    @classmethod
    def name(cls) -> str:
        return cls._name

    @abstractmethod
    def _parse(self) -> T:
        pass

    def parse(self) -> T:
        if self._cached is None:
            self._cached = self._parse()

        return self._cached

    def is_cached(self) -> bool:
        return self._cached is not None


class LocalReadParser(BaseParser, ABC):
    _local_config: Mapping[str, Any]
    _workspace: Path

    def set_local_cfg(self, local_config: Mapping[str, Any]) -> LocalReadParser:
        self._local_config = local_config
        self._cached = None
        return self

    @property
    def workspace(self) -> Path:
        return self._workspace

    @workspace.setter
    def workspace(self, new_path: Path) -> None:
        self._workspace = new_path
