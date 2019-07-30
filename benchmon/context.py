# coding: UTF-8

import logging
from typing import Any, Dict, Type

from abc import ABCMeta, abstractmethod
from aiofile_linux import AIOContext

# FIXME: hard coded
_aio_context = AIOContext(128)


def aio_context() -> AIOContext:
    return _aio_context


class Context:
    __slots__ = ('_variable_dict',)

    _variable_dict: Dict[Type, Any]

    def __init__(self) -> None:
        self._variable_dict = dict()

    def _assign(self, val: Any, cls: Type = None) -> None:
        if cls is None:
            cls = type(val)
        self._variable_dict[cls] = val

    @property
    def logger(self) -> logging.Logger:
        return self._variable_dict[logging.Logger]


class ContextReadable(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def of(cls, context: Context) -> Any:
        pass
