# coding: UTF-8

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from ..base import BaseBenchmark


class BaseConstraint(metaclass=ABCMeta):
    """
    :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 실행 전후로 환경을 설정한다.

    내부 메소드들은 :meth:`on_init` -> :meth:`on_start` -> :meth:`on_destroy` 순서로 호출된다.

    .. note::

        * 모든 constraint 클래스들은 직접 객체화하지 않고, 각 클래스에 알맞는
          :class:`빌더 <bench_toolbox.benchmark.constraints.base_builder.BaseBuilder>` 를 통해 객체화한다.

        * 이 클래스를 상속받는 constraints들은 재사용 가능해야한다.
          즉, :meth:`on_init` -> :meth:`on_start` -> :meth:`on_destroy` -> :meth:`on_init` 처럼 같이 constraints를
          재활용할 때 아무 문제가 없어야한다.

    .. seealso::

        역할과 설명
            :mod:`bench_toolbox.benchmark.constraints` 참조
    """

    _benchmark: BaseBenchmark

    def __new__(cls: Type[BaseConstraint], bench: BaseBenchmark) -> BaseConstraint:
        """
        :param bench: 이 constraint가 붙여질 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>`
        :type bench: bench_toolbox.benchmark.base.BaseBenchmark
        """
        obj: BaseConstraint = super().__new__(cls)

        obj._benchmark = bench

        return obj

    async def on_init(self) -> None:
        """
        외부에게서 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 에게 실행을 명령받자마자 호출된다.
        즉, 벤치마크 실행 명령과 실제 벤치마크의 실행 사이에서 호출된다.
        때문에 앞으로 실행될 벤치마크의 PID 등 runtime에서만 얻을 수 있는 정보를 알 수 없지만,
        벤치마크의 실행 설정은 알 수 있다. (e.g. 벤치마크 이름, cgroup 설정 등)

        주로 해당 constraint가 사용할 자원을 할당받는다.
        """
        pass

    @abstractmethod
    async def on_start(self) -> None:
        """
        :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 가 실제로 실행 되자마자 호출된다.
        즉, 벤치마크의 실제 실행과 모니터의 실행 사이에 호출된다.
        따라서 무조건 :meth:`on_init` 다음에 호출된다.

        실제 실행중인 벤치마크의 PID같은 정보를 얻을 수 있다.
        """
        pass

    @abstractmethod
    async def on_destroy(self) -> None:
        """
        어떤 이유에서든지 (e.g. 정상종료, 에러 발생) :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>`
        가 종료된 후에 호출된다.
        따라서 벤치마크의 PID 등 runtime에서만 얻을 수 있는 정보를 알 수 없지만,
        벤치마크의 실행 설정은 알 수 있다. (e.g. 벤치마크 이름, cgroup 설정 등)

        주로 해당 constraint가 할당받은 자원을 할당해제한다.
        """
        pass
