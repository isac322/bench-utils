# coding: UTF-8

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Generic, Mapping, Optional, TYPE_CHECKING, TypeVar

from .. import validate_and_load

if TYPE_CHECKING:
    from pathlib import Path

_DT = TypeVar('_DT')


class BaseParser(Generic[_DT], metaclass=ABCMeta):
    """
    모든 파서의 부모 클래스.
    자식 클래스는 :meth:`_parse` 를 override해야한다.
    :meth:`parse` 는 파싱을 할 경우 결과를 자동으로 캐싱 해높으며, :meth:`is_cached` 를 통해 존재 유무를 확인할 수 있다.

    이 클래스만으로는 외부의 설정을 읽지 못하고 :mod:`benchmon.configs` 안에 있는 설정 파일만 읽어야 한다.
    :class:`LocalReadParser` 같이 외부의 설정파일을 읽고 싶은 경우 다른 종류의 파서 클래스를 정의하고 구현해야한다.
    """
    __slots__ = ('_cached',)

    _cached: Optional[_DT]

    def __init__(self) -> None:
        self._cached = None

    @abstractmethod
    def _parse(self) -> _DT:
        """
        실제로 파싱을 진행하는 부분.
        자식클래스별로 내용을 다르게 구현 해야한다.

        :return: 파싱을 한 결과
        :rtype: _DT
        """
        pass

    def parse(self) -> _DT:
        """
        :meth:`_parse` 로 실제 파싱을 진행한 결과를 캐싱한다.
        캐싱이 된 상태에서 이 메소드가 다시 호출된다면, :meth:`_parse` 를 재호출하지 않고 캐싱된 결과를 반환한다.

        :return: 파싱을 한 결과
        :rtype: _DT
        """
        if self._cached is None:
            self._cached = self._parse()

        return self._cached

    def is_cached(self) -> bool:
        """
        파서가 파싱 결과를 캐싱 하였는지 확인한다.

        :return: 캐싱 유무
        :rtype: bool
        """
        return self._cached is not None


_LRP = TypeVar('_LRP', bound='LocalReadParser')


class LocalReadParser(BaseParser[_DT], ABC):
    """
    :class:`BaseParser` 와 다르게 외부에 존재하는 local `config.json` 파일을 읽어서 파싱한다.
    """
    __slots__ = ('_local_config', '_workspace')

    _local_config: Mapping[str, Any]
    _workspace: Path

    def __init__(self, workspace: Path) -> None:
        super().__init__()

        self._local_config = validate_and_load(workspace / 'config.json')
        self._workspace = workspace

    def reload_local_cfg(self: _LRP) -> _LRP:
        """
        캐싱된 결과를 무시하고 다시 파싱한다.
        `config.json` 의 내용이 바뀔 경우 유용하다.

        :return: Method chaining을 위한 파서 객체 그대로 반환
        :rtype: benchmon.configs.parsers.base.LocalReadParser
        """
        self._local_config = validate_and_load(self._workspace / 'config.json')
        self._cached = None
        return self
