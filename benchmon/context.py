# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Type

from aiofile_linux import AIOContext

# FIXME: hard coded
_aio_context = AIOContext(128)


def aio_context() -> AIOContext:
    return _aio_context


class Context:
    _variable_dict: Dict[Type, Any]

    def __init__(self) -> None:
        self._variable_dict = dict()

    def _assign(self, cls: Type, val: Any) -> None:
        self._variable_dict[cls] = val


class ContextReadable(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def of(cls, context: Context) -> Any:
        pass
