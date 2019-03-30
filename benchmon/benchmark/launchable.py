# coding: UTF-8

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, Tuple, Type

import psutil

from .base import BaseBenchmark
from .base_builder import BaseBuilder
from .drivers import gen_driver
from .drivers.engines import CGroupEngine
from ..monitors.pipelines import DefaultPipeline

if TYPE_CHECKING:
    from .drivers import BenchDriver
    from .. import Context
    from ..configs.containers import LaunchableConfig, PrivilegeConfig
    from ..monitors.pipelines import BasePipeline


class LaunchableBenchmark(BaseBenchmark):
    """
    벤치마크 중에서 :class:`~benchmon.benchmark.drivers.base.BenchDriver` 를 사용해서 프로세스를 생성하는 식으로 실행하는
    벤치마크들을 (e.g. NPB, PARSEC) 위한 클래스.

    `드라이버` 객체를 하나씩 가진다.
    """

    _bench_driver: BenchDriver
    _bench_config: LaunchableConfig

    @classmethod
    def of(cls, context: Context) -> Optional[LaunchableBenchmark]:
        # noinspection PyProtectedMember
        return context._variable_dict.get(cls)

    def __new__(cls: Type[LaunchableBenchmark],
                launchable_config: LaunchableConfig,
                pipeline: BasePipeline,
                logger_level: int = logging.INFO) -> LaunchableBenchmark:
        obj: LaunchableBenchmark = super().__new__(cls, launchable_config, pipeline, logger_level)

        obj._bench_driver = gen_driver(launchable_config.name, launchable_config.num_of_threads, CGroupEngine(obj))

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

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
    def launched_time(self) -> float:
        return self._bench_driver.created_time

    @property
    def pid(self) -> int:
        return self._bench_driver.pid

    @property
    def is_running(self) -> bool:
        return self._bench_driver.is_running

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
        _cur_obj: LaunchableBenchmark

        def __init__(self, launchable_config: LaunchableConfig, privilege_config: PrivilegeConfig,
                     logger_level: int = logging.INFO) -> None:
            super().__init__(launchable_config, privilege_config, logger_level)

        def _init_pipeline(self) -> DefaultPipeline:
            return DefaultPipeline()

        def _init_bench_obj(self, pipeline: BasePipeline) -> LaunchableBenchmark:
            return LaunchableBenchmark.__new__(LaunchableBenchmark, self._bench_config, pipeline, self._logger_level)
