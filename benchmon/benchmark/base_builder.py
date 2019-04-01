# coding: UTF-8

from __future__ import annotations

import warnings
from abc import ABCMeta, abstractmethod
from typing import Dict, Generic, List, TYPE_CHECKING, Type, TypeVar

from .base import BaseBenchmark
from .constraints.base import BaseConstraint
from .. import Context
from ..monitors.idle import IdleMonitor

if TYPE_CHECKING:
    from ..configs.containers import BenchConfig, PrivilegeConfig
    from ..monitors import BaseMonitor, MonitorData
    from ..monitors.messages.handlers import BaseHandler
    from ..monitors.pipelines import BasePipeline

_BT = TypeVar('_BT', bound=BaseBenchmark)


class BaseBuilder(Generic[_BT], metaclass=ABCMeta):
    """
    :class:`~benchmon.benchmark.base.BaseBenchmark` 의 자식 클래스들은 생성자를 통해 객체화 할 수 없고,
    이 클래스를 통해서만 객체화 해야한다.

    생성할 벤치마크의 모니터와 제약은 이 클래스를 통해 :meth:`finalize` 하기 전에 추가 해야하며, 그 이후에는 추가하거나 삭제할 수 없다.

    사용 예:

    .. code-block:: python

        bench_cfg: LaunchableConfig = ...

        bench: LaunchableBenchmark = bench_cfg.generate_builder(logging.DEBUG)
            .add_constraint(RabbitMQConstraint(rabbit_mq_config))
            .add_monitor(RuntimeMonitor())
            .add_monitor(PowerMonitor())
            .add_handler(StorePerf())
            .add_handler(StoreRuntime())
            .add_handler(StoreResCtrl())
            .add_handler(PrintHandler())
            .finalize()
    """
    _is_finalized: bool = False
    _bench_config: BenchConfig
    _privilege_config: PrivilegeConfig
    _pipeline: BasePipeline
    _cur_obj: _BT
    _context: Context
    _logger_level: int
    _monitors: List[BaseMonitor[MonitorData]]
    _constraints: Dict[Type[BaseConstraint], BaseConstraint]

    def __init__(self, bench_config: BenchConfig, privilege_config: PrivilegeConfig, logger_level: int) -> None:
        self._bench_config = bench_config
        self._privilege_config = privilege_config
        self._logger_level = logger_level

        self._monitors = list()
        self._constraints = dict()

        self._pipeline = self._init_pipeline()
        self._cur_obj = self._init_bench_obj(self._pipeline)
        self._context = self._init_context_var()

        for constraint in bench_config.constraints:
            self.add_constraint(constraint)

    @abstractmethod
    def _init_pipeline(self) -> BasePipeline:
        pass

    @abstractmethod
    def _init_bench_obj(self, pipeline: BasePipeline) -> _BT:
        pass

    # noinspection PyProtectedMember
    def _init_context_var(self) -> Context:
        """
        모니터와 제약에서 쓰일 Context 객체를 생성하고, 값들을 설정한다.

        :return: 이 객체에서 쓰일 Context 객체
        :rtype: benchmon.context.Context
        """
        context = Context()

        context._assign(type(self._cur_obj), self._cur_obj)
        context._assign(type(self._pipeline), self._pipeline)
        context._assign(type(self._privilege_config), self._privilege_config)

        return context

    def add_handler(self, handler: BaseHandler) -> BaseBuilder[_BT]:
        """
        생성할 벤치마크가 가지는 파이프라인에 `handler` 를 추가한다.

        :param handler: 추가할 메시지 핸들러
        :type handler: benchmon.monitors.messages.handlers.base.BaseHandler
        :return: Method chaining을 위한 빌더 객체 그대로 반환
        :rtype: benchmon.benchmark.base_builder.BaseBuilder
        """
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._pipeline.add_handler(handler)

        return self

    def add_monitor(self, monitor: BaseMonitor) -> BaseBuilder[_BT]:
        """
        생성할 벤치마크가 가지는 모니터에 `monitor` 를 추가한다.

        :param monitor: 추가할 모니터
        :type monitor: benchmon.monitors.base.BaseMonitor
        :return: Method chaining을 위한 빌더 객체 그대로 반환
        :rtype: benchmon.benchmark.base_builder.BaseBuilder
        """
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._monitors.append(monitor)

        return self

    def add_constraint(self, constraint: BaseConstraint) -> BaseBuilder[_BT]:
        """
        생성할 벤치마크가 가지는 제약에 `constraint` 를 추가한다.

        :param constraint: 추가할 제약
        :type constraint: benchmon.benchmark.constraints.base.BaseConstraint
        :return: Method chaining을 위한 빌더 객체 그대로 반환
        :rtype: benchmon.benchmark.base_builder.BaseBuilder
        """
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')
        elif type(constraint) in self._constraints:
            warnings.warn(f'{type(constraint)} type constraint is already added')

        self._constraints[type(constraint)] = constraint

        return self

    def _finalize(self) -> None:
        """
        :meth:`finalize` 안에서 호출되며, 이 클래스의 자식 클레스에서는 :meth:`finalize` 메소드보다 이 메소드를 override해서
        그 클래스가 finalize 전에 해야할 동작을 서술하는것이 좋다.
        """
        if len(self._monitors) is 0:
            self.add_monitor(IdleMonitor())

    def finalize(self) -> _BT:
        """
        벤치마크 객체를 실제로 생성한다.

        이 클래스의 자식 클래스가 객체 생성과정을 수정하고싶은 경우 이 메소드를 override 하는것 보다
        :meth:`_finalize` 메소드를 수정하는 것이 바람직하다.

        :return: 생성된 벤치마크 객체
        :rtype: benchmon.benchmark.base.BaseBenchmark
        """
        if self._is_finalized:
            raise AssertionError('Can\'t not reuse the finalized builder.')

        self._finalize()

        self._cur_obj._monitors = tuple(self._monitors)
        self._cur_obj._constraints = tuple(self._constraints.values())
        self._cur_obj._context_variable = self._context

        self._is_finalized = True

        return self._cur_obj
