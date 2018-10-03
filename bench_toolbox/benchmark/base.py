# coding: UTF-8

from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import ClassVar, TYPE_CHECKING, Tuple, Type

from coloredlogs import ColoredFormatter

from ..monitors.pipelines import DefaultPipeline

if TYPE_CHECKING:
    from ..configs.containers import BenchConfig
    from ..monitors import BaseMonitor, MonitorData
    from ..monitors.pipelines import BasePipeline
    # because of circular import
    from .constraints.base import BaseConstraint


class BaseBenchmark(metaclass=ABCMeta):
    _file_formatter: ClassVar[ColoredFormatter] = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] (%(funcName)s:%(lineno)d in %(filename)s) $ %(message)s')

    _bench_config: BenchConfig
    _identifier: str
    _monitors: Tuple[BaseMonitor[MonitorData], ...]
    _constraints: Tuple[BaseConstraint, ...]
    _pipeline: BasePipeline
    _log_path: Path

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
        logger.addHandler(fh)

        if not silent:
            stream_handler = logging.StreamHandler()
            formatter: ColoredFormatter = ColoredFormatter(
                    f'%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)-{self._bench_config.width_in_log}s '
                    f'$ %(message)s')
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        # initialize constraints & pipeline

        if len(self._constraints) is not 0:
            await asyncio.wait(tuple(con.on_init() for con in self._constraints))

        await self._pipeline.on_init()

    @abstractmethod
    async def monitor(self) -> None:
        pass

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    def resume(self) -> None:
        pass

    @abstractmethod
    async def join(self) -> None:
        pass

    def _remove_logger_handlers(self) -> None:
        logger: logging.Logger = logging.getLogger(self._identifier)

        for handler in tuple(logger.handlers):  # type: logging.Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    @abstractmethod
    def group_name(self) -> str:
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
