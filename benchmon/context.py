# coding: UTF-8

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Type


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
