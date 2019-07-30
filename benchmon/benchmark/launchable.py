# coding: UTF-8

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, Tuple, Type, TypeVar

import psutil

from .base import BaseBenchmark
from .base_builder import BaseBuilder
from .drivers import gen_driver
from .drivers.engines import BaseEngine, CGroupEngine
from ..configs.containers import LaunchableConfig
from ..monitors.pipelines import DefaultPipeline

if TYPE_CHECKING:
    from .constraints import BaseConstraint
    from .drivers import BenchDriver
    from .. import Context
    from ..configs.containers import PrivilegeConfig
    from ..monitors import BaseMonitor
    from ..monitors.pipelines import BasePipeline

    _CST_T = TypeVar('_CST_T', bound=BaseConstraint)
    _MON_T = TypeVar('_MON_T', bound=BaseMonitor)

_CFG_T = TypeVar('_CFG_T', bound=LaunchableConfig)


class LaunchableBenchmark(BaseBenchmark[_CFG_T]):
    """
    벤치마크 중에서 :class:`~benchmon.benchmark.drivers.base.BenchDriver` 를 사용해서 프로세스를 생성하는 식으로 실행하는
    벤치마크들을 (e.g. NPB, PARSEC) 위한 클래스.

    `드라이버` 객체를 하나씩 가진다.
    """
    _bench_driver: BenchDriver

    @classmethod
    def of(cls, context: Context) -> Optional[LaunchableBenchmark]:
        # noinspection PyProtectedMember
        return context._variable_dict.get(cls)

    def __new__(cls: Type[BaseBenchmark],
                launchable_config: _CFG_T,
                constraints: Tuple[_CST_T, ...],
                monitors: Tuple[_MON_T, ...],
                pipeline: BasePipeline,
                privilege_config: PrivilegeConfig) -> LaunchableBenchmark:
        # noinspection PyTypeChecker
        obj: LaunchableBenchmark = super().__new__(
                cls,
                launchable_config,
                constraints,
                monitors,
                pipeline,
                privilege_config
        )

        obj._bench_driver = gen_driver(launchable_config.name)

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(type(self).__name__))

    def pause(self) -> None:
        logging.getLogger(self._identifier).info('pausing...')

        self._bench_driver.pause()

    def resume(self) -> None:
        logging.getLogger(self._identifier).info('resuming...')

        self._bench_driver.resume()

    async def _start(self, context: Context) -> None:
        await self._bench_driver.run(context)

    async def kill(self) -> None:
        logger = logging.getLogger(self._identifier)
        logger.info('stopping...')

        try:
            self._bench_driver.stop()
        except (psutil.NoSuchProcess, ProcessLookupError) as e:
            logger.debug(f'Process already killed : {e}')

    @property
    def launched_time(self) -> Optional[float]:
        return self._bench_driver.created_time

    @property
    def pid(self) -> Optional[int]:
        return self._bench_driver.pid

    @property
    def is_running(self) -> bool:
        return self._bench_driver.is_running()

    @property
    def group_name(self) -> str:
        if self.is_running:
            return '{}_{}'.format(self._bench_driver.name, self._bench_driver.pid)
        else:
            return self._identifier

    def all_child_tid(self) -> Tuple[int, ...]:
        return self._bench_driver.all_child_tid()

    async def join(self) -> None:
        await self._bench_driver.join()

    class Builder(BaseBuilder['LaunchableBenchmark']):
        _bench_config: LaunchableConfig

        def __init__(self,
                     launchable_config: LaunchableConfig,
                     privilege_config: PrivilegeConfig,
                     logger_level: int = logging.INFO) -> None:
            super().__init__(launchable_config, privilege_config, logger_level)

        @classmethod
        def _init_pipeline(cls) -> DefaultPipeline:
            return DefaultPipeline()

        def _init_context_var(self, benchmark: LaunchableBenchmark, logger_level: int) -> None:
            super()._init_context_var(benchmark, logger_level)

            # noinspection PyProtectedMember
            benchmark._context_variable._assign(CGroupEngine, BaseEngine)

        def _finalize(self) -> LaunchableBenchmark:
            return LaunchableBenchmark.__new__(
                    LaunchableBenchmark,
                    self._bench_config,
                    tuple(self._constraints.values()),
                    tuple(self._monitors),
                    self._pipeline,
                    self._privilege_config
            )
