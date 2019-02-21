# coding: UTF-8

from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import ClassVar, Optional, TYPE_CHECKING, Tuple, Type

from coloredlogs import ColoredFormatter

from .. import Context, ContextReadable
from ..monitors.pipelines import DefaultPipeline

if TYPE_CHECKING:
    from ..configs.containers import BenchConfig
    from ..monitors import BaseMonitor, MonitorData
    from ..monitors.pipelines import BasePipeline
    # because of circular import
    from .constraints.base import BaseConstraint


class BaseBenchmark(ContextReadable, metaclass=ABCMeta):
    _file_formatter: ClassVar[ColoredFormatter] = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] (%(funcName)s:%(lineno)d in %(filename)s) $ %(message)s')

    _bench_config: BenchConfig
    _identifier: str
    _monitors: Tuple[BaseMonitor[MonitorData], ...]
    _constraints: Tuple[BaseConstraint, ...]
    _pipeline: BasePipeline
    _log_path: Path
    _context_variable: Context

    @classmethod
    def of(cls, context: Context) -> Optional[BaseBenchmark]:
        # noinspection PyProtectedMember
        for c, v in context._variable_dict.items():
            if issubclass(c, cls):
                return v

        return None

    def __new__(cls: Type[BaseBenchmark],
                bench_config: BenchConfig,
                logger_level: int = logging.INFO) -> BaseBenchmark:
        obj: BaseBenchmark = super().__new__(cls)

        obj._bench_config = bench_config
        obj._identifier = bench_config.identifier

        obj._monitors: Tuple[BaseMonitor[MonitorData], ...] = tuple()
        obj._pipeline: BasePipeline = DefaultPipeline()

        # setup for logger
        log_dir = bench_config.workspace / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        obj._log_path: Path = log_dir / f'{bench_config.identifier}.log'

        logger = logging.getLogger(bench_config.identifier)
        logger.setLevel(logger_level)

        return obj

    async def start_and_pause(self, silent: bool = False) -> None:
        self._remove_logger_handlers()

        # setup for loggers
        logger = logging.getLogger(self._identifier)

        fh = logging.FileHandler(self._log_path, mode='w')
        fh.setFormatter(BaseBenchmark._file_formatter)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

        if not silent:
            stream_handler = logging.StreamHandler()
            formatter: ColoredFormatter = ColoredFormatter(
                    f'%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)-{self._bench_config.width_in_log}s '
                    f'$ %(message)s')
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        # noinspection PyBroadException
        try:
            # initialize constraints & pipeline
            if len(self._constraints) is not 0:
                await asyncio.wait(tuple(con.on_init() for con in self._constraints))
                logger.debug('Constraints are initialized')

            await self._pipeline.on_init()
            logger.debug('Pipe is initialized')

            logger.info('Starting benchmark...')
            await self._start()
            logger.info(f'The benchmark has started. pid : {self.pid}')

            logger.debug('Pausing benchmark...')
            self.pause()

        except asyncio.CancelledError:
            logger.debug(f'The task cancelled')
            if self.is_running:
                await self.kill()

            await self._destroy()

        except Exception as e:
            logger.critical(f'The following errors occurred during startup : {e}')
            if self.is_running:
                await self.kill()

            await self._destroy()

    async def monitor(self) -> None:
        logger = logging.getLogger(self._identifier)
        logger.info('start monitoring...')

        monitoring_tasks: Optional[asyncio.Task] = None

        # noinspection PyBroadException
        try:
            if len(self._constraints) is not 0:
                await asyncio.wait(tuple(con.on_start() for con in self._constraints))

            await asyncio.wait(tuple(mon.on_init() for mon in self._monitors))
            monitoring_tasks = asyncio.create_task(asyncio.wait(tuple(mon.monitor() for mon in self._monitors)))

            await asyncio.wait((self.join(), monitoring_tasks),
                               return_when=asyncio.FIRST_COMPLETED)

            if self.is_running:
                await self.join()
            else:
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        except asyncio.CancelledError:
            logger.debug(f'The task cancelled')
            if self.is_running:
                await self.kill()
            if monitoring_tasks is not None and not monitoring_tasks.done():
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        except Exception as e:
            logger.critical(f'The following errors occurred during monitoring : {e}')
            if self.is_running:
                await self.kill()
            if monitoring_tasks is not None and not monitoring_tasks.done():
                await asyncio.wait(tuple(mon.stop() for mon in self._monitors))
                await monitoring_tasks

        finally:
            logger.info('The benchmark is ended.')

            # destroy monitors
            await asyncio.wait(tuple(mon.on_end() for mon in self._monitors))
            await asyncio.wait(tuple(mon.on_destroy() for mon in self._monitors))

            await self._destroy()

    async def _destroy(self) -> None:
        # destroy constraints
        if len(self._constraints) is not 0:
            await asyncio.wait(tuple(con.on_destroy() for con in self._constraints))

        # destroy pipeline
        await self._pipeline.on_end()
        await self._pipeline.on_destroy()

        self._remove_logger_handlers()

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    def resume(self) -> None:
        pass

    @abstractmethod
    async def join(self) -> None:
        pass

    @abstractmethod
    async def _start(self) -> None:
        pass

    @abstractmethod
    async def kill(self) -> None:
        pass

    def _remove_logger_handlers(self) -> None:
        logger: logging.Logger = logging.getLogger(self._identifier)

        for handler in tuple(logger.handlers):  # type: logging.Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    # noinspection PyProtectedMember
    def _initialize_context(self) -> Context:
        context = Context()

        context._assign(self.__class__, self)

        return context

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    @abstractmethod
    def group_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        pass

    @property
    @abstractmethod
    def pid(self) -> int:
        pass

    @property
    def type(self) -> str:
        return self._bench_config.type

    @abstractmethod
    def all_child_tid(self) -> Tuple[int, ...]:
        pass
