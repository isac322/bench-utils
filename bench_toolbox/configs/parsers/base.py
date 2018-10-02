# coding: UTF-8

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import Any, ClassVar, Mapping, Optional, Type


class BaseParser(metaclass=ABCMeta):
    _name: ClassVar[str]
    TARGET: ClassVar[Type]
    _cached: Optional[TARGET]

    def __init__(self) -> None:
        self._cached = None

    @classmethod
    def name(cls) -> str:
        return cls._name

    @abstractmethod
    def _parse(self) -> BaseParser.TARGET:
        pass

    def parse(self) -> BaseParser.TARGET:
        if self._cached is None:
            self._cached = self._parse()

        return self._cached

    def is_cached(self) -> bool:
        return self._cached is not None


class LocalReadParser(BaseParser, ABC):
    _local_config: Mapping[str, Any]

    def set_local_cfg(self, local_config: Mapping[str, Any]) -> LocalReadParser:
        self._local_config = local_config
        self._cached = None
        return self
