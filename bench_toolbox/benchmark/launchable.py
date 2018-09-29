# coding: UTF-8

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import CancelledError
from pathlib import Path
from typing import Optional, Tuple, Type

import psutil

from .base import BaseBenchmark
from .base_builder import BaseBuilder
from .decorators.benchmark import ensure_invoked, ensure_not_running, ensure_running
from .drivers import BenchDriver, gen_driver
from .drivers.engines.cgroup import CGroupEngine
from ..containers import BenchConfig
from ..monitors import MonitorData
from ..monitors.base import BaseMonitor
from ..monitors.base_builder import BaseBuilder as MonitorBuilder
from ..monitors.idle import IdleMonitor
from ..monitors.messages.handlers.base import BaseHandler


class LaunchableBenchmark(BaseBenchmark):
    _bench_driver: BenchDriver

    def __new__(cls: Type[LaunchableBenchmark],
                bench_config: BenchConfig,
                workspace: Path,
                logger_level: int = logging.INFO) -> LaunchableBenchmark:
        obj: LaunchableBenchmark = super().__new__(cls, bench_config.identifier,
                                                   bench_config.wl_type, workspace, logger_level)

        obj._bench_driver = gen_driver(bench_config.name, bench_config.num_of_threads, CGroupEngine(obj))

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    @ensure_not_running
    async def start_and_pause(self, silent: bool = False) -> None:
        await super().start_and_pause(silent)

        logger = logging.getLogger(self._identifier)

        # noinspection PyBroadException
        try:
            logger.info('Starting benchmark...')
            await self._bench_driver.run()
            logger.info(f'The benchmark has started. pid : {self._bench_driver.pid}')

            self.pause()

        except CancelledError as e:
            logger.debug(f'The task cancelled : {e}')
            if self._bench_driver.is_running:
                self._stop()

                # destroy constraints
                if len(self._constraints) is not 0:
                    await asyncio.wait(tuple(con.on_destroy() for con in self._constraints))

                # destroy pipeline
                await self._pipeline.on_end()
                await self._pipeline.on_destroy()

        except Exception as e:
            logger.critical(f'The following errors occurred during startup : {e}')
            if self.is_running:
                self._stop()

                # destroy constraints
                if len(self._constraints) is not 0:
                    await asyncio.wait(tuple(con.on_destroy() for con in self._constraints))

                # destroy pipeline
                await self._pipeline.on_end()
                await self._pipeline.on_destroy()

    @ensure_running
    async def monitor(self) -> None:
        logger = logging.getLogger(self._identifier)

        monitoring_tasks: Optional[asyncio.Task] = None

        # noinspection PyBroadException
        try:
            if len(self._constraints) is not 0:
                await asyncio.wait(tuple(con.on_start() for con in self._constraints))

            await asyncio.wait(tuple(mon.on_init() for mon in self._monitors))
            monitoring_tasks = asyncio.create_task(asyncio.wait(tuple(mon.monitor() for mon in self._monitors)))

            await asyncio.wait((self._bench_driver.join(), monitoring_tasks),
                               return_when=asyncio.FIRST_COMPLETED)

            if self.is_running:
                await self._bench_driver.join()
            else:
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        except CancelledError as e:
            logger.debug(f'The task cancelled : {e}')
            if self.is_running:
                self._stop()
            if monitoring_tasks is not None and not monitoring_tasks.done():
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        except Exception as e:
            logger.critical(f'The following errors occurred during monitoring : {e}')
            if self.is_running:
                self._stop()
            if monitoring_tasks is not None and not monitoring_tasks.done():
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        finally:
            logger.info('The benchmark is ended.')

            # destroy monitors
            await asyncio.wait(tuple(mon.on_end() for mon in self._monitors))
            await asyncio.wait(tuple(mon.on_destroy() for mon in self._monitors))

            # destroy constraints
            if len(self._constraints) is not 0:
                await asyncio.wait(tuple(con.on_destroy() for con in self._constraints))

            # destroy pipeline
            await self._pipeline.on_end()
            await self._pipeline.on_destroy()

            self._remove_logger_handlers()

    @ensure_running
    def pause(self) -> None:
        logging.getLogger(self._identifier).info('pausing...')

        self._bench_driver.pause()

    @ensure_running
    def resume(self) -> None:
        logging.getLogger(self._identifier).info('resuming...')

        self._bench_driver.resume()

    @ensure_running
    def _stop(self) -> None:
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
        def __init__(self, bench_config: BenchConfig, workspace: Path, logger_level: int = logging.INFO) -> None:
            super().__init__()

            self._cur_obj: LaunchableBenchmark = LaunchableBenchmark.__new__(LaunchableBenchmark, bench_config,
                                                                             workspace, logger_level)

            for builder in bench_config.constraint_builders:
                self.build_constraint(builder)

        def _build_monitor(self, monitor_builder: MonitorBuilder) -> BaseMonitor[MonitorData]:
            return monitor_builder \
                .set_benchmark(self._cur_obj) \
                .set_emitter(self._cur_obj._pipeline.on_message) \
                .finalize()

        def add_handler(self, handler: BaseHandler) -> LaunchableBenchmark.Builder:
            self._cur_obj._pipeline.add_handler(handler)
            return self

        def _finalize(self) -> None:
            if len(self._monitors) is 0:
                self.build_monitor(IdleMonitor.Builder())
