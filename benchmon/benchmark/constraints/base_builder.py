# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, TYPE_CHECKING, TypeVar

from .base import BaseConstraint

if TYPE_CHECKING:
    from ..base import BaseBenchmark

T = TypeVar('T', bound=BaseConstraint)


class BaseBuilder(Generic[T], metaclass=ABCMeta):
    """
    :class:`constraint <benchmon.benchmark.constraints.base.BaseConstraint>` 객체를 생성하기 위한 빌더.

    모든 constraint 클래스는 이 빌더 클래스를 상속받은 빌더를 통해 객체화 되어야한다.
    따라서, 새로운 constraint 클래스를 만들었을 때는 항상 그 constraint 클래스를 위한 빌더를 작성 해야한다.
    그 빌더는 반드시 이 클래스를 상속 받아야하며, 생성자를 통해 외부로부터 변수를 들여올 수 있다.

    하나의 빌더는 여러개의 constraint를 만들어낼 수 있어야한다.
    """

    @abstractmethod
    def finalize(self, benchmark: BaseBenchmark) -> T:
        """
        `benchmark` 를 위해 이 빌더가 만들 수 있는 constraint 객체를 객체화하여 반환한다.

        :param benchmark: 실행 전후의 환경 설정을 할 벤치마크
        :type benchmark: benchmon.benchmark.base.BaseBenchmark
        :return: 이 빌더가 만들 수 있는 constraint 객체
        :rtype: benchmon.benchmark.constraints.base.BaseConstraint
        """
        pass
