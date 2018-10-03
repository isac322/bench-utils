# coding: UTF-8

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Tuple, Type

import psutil

from .base import BaseBenchmark
from .base_builder import BaseBuilder
from .decorators.benchmark import ensure_invoked, ensure_running
from .drivers import gen_driver
from .drivers.engines import CGroupEngine

if TYPE_CHECKING:
    from .drivers import BenchDriver
    from ..configs.containers import LaunchableConfig


class LaunchableBenchmark(BaseBenchmark):
    _bench_driver: BenchDriver
    _bench_config: LaunchableConfig

    def __new__(cls: Type[LaunchableBenchmark],
                launchable_config: LaunchableConfig,
                logger_level: int = logging.INFO) -> LaunchableBenchmark:
        obj: LaunchableBenchmark = super().__new__(cls, launchable_config, logger_level)

        obj._bench_driver = gen_driver(launchable_config.name, launchable_config.num_of_threads, CGroupEngine(obj))

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    @ensure_running
    def pause(self) -> None:
        logging.getLogger(self._identifier).info('pausing...')

        self._bench_driver.pause()

    @ensure_running
    def resume(self) -> None:
        logging.getLogger(self._identifier).info('resuming...')

        self._bench_driver.resume()

    async def _start(self) -> None:
        await self._bench_driver.run()

    @ensure_running
    async def kill(self) -> None:
        logger = logging.getLogger(self._identifier)
        logger.info('stopping...')

        try:
            self._bench_driver.stop()
        except (psutil.NoSuchProcess, ProcessLookupError) as e:
            logger.debug(f'Process already killed : {e}')

    @property
    @ensure_invoked
    def launched_time(self) -> float:
        return self._bench_driver.created_time

    @property
    @ensure_running
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

    @ensure_running
    def all_child_tid(self) -> Tuple[int, ...]:
        return self._bench_driver.all_child_tid()

    @ensure_running
    async def join(self) -> None:
        await self._bench_driver.join()

    class Builder(BaseBuilder['LaunchableBenchmark']):
        _cur_obj: LaunchableBenchmark

        def __init__(self, launchable_config: LaunchableConfig, logger_level: int = logging.INFO) -> None:
            super().__init__()

            self._cur_obj = LaunchableBenchmark.__new__(LaunchableBenchmark, launchable_config, logger_level)

            for builder in launchable_config.constraint_builders:
                self.build_constraint(builder)
