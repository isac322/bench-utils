# coding: UTF-8

from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod
from asyncio import Future
from typing import ClassVar, Coroutine, Iterable, Optional, Set, TYPE_CHECKING, Tuple, Type, TypeVar, Union

from coloredlogs import ColoredFormatter

from .. import Context, ContextReadable
from ..configs.containers import PrivilegeConfig
from ..exceptions import BenchNotFoundError
from ..utils.privilege import drop_privilege

if TYPE_CHECKING:
    from pathlib import Path

    # because of circular import
    from .constraints import BaseConstraint
    from ..configs.containers import BenchConfig
    from ..monitors import BaseMonitor
    from ..monitors.pipelines import BasePipeline

    _MON_T = TypeVar('_MON_T', bound=BaseMonitor)


class BaseBenchmark(ContextReadable, metaclass=ABCMeta):
    """
    벤치마크의 실행과 일시 정지, 모니터링을 담당하는 high-level 클래스들의 부모 클래스.

    각각의 특성에 따라 이 클래스를 상속받고, abstractmethod들을 채워야한다.

    벤치마크의 역할:

    * 벤치마크 실행
        * :meth:`_start` 를 override 해야한다.
        * 상황에 따라서 :mod:`드라이버 <benchmon.benchmark.drivers>` 를 사용하여 벤치마크를 실행 할 수도 있다.
    * 벤치마크 일시 정지와 재시작
        * 벤치마크의 특성에 따라서 지원할 수도 안할 수도 있다.
    * 벤치마크 모니터링
        * 이 클래스는 :class:`모니터 <benchmon.monitors.base.BaseMonitor>` 를 여러개 가지며,
          벤치마크 실행 후 :meth:`monitor` 로 모니터링을 시작할 수 있다.
        * 벤치마크에 `모니터` 를 등록하는 방법은 각 벤치마크의 빌더를 통해서 할 수 있다.
            * 즉 벤치마크 생성시 한번에 모든 `모니터` 를 등록 해야하며, 중간에 `모니터` 를 추가하거나 삭제할 수 없다.
        * `모니터` 를 통해 생성된 데이터는 :class:`파이프라인 <benchmon.monitors.pipelines.base.BasePipeline>` 를 통해 전단된다.
    * 각종 제약 (constraint)
        * 이 클래스는 :mod:`제약 <benchmon.benchmark.constraints>` 을 여러개 가지며,
          벤치마크의 실행 전후로 자원 할당 등과 같은 역할들을 담당하게 할 수 있다.
        * 벤치마크에 `제약` 을 등록하는 방법은 각 벤치마크의 빌더를 통해서 할 수 있다.
            * 즉 벤치마크 생성시 한번에 모든 `제약` 을 등록 해야하며, 중간에 `제약` 을 추가하거나 삭제할 수 없다.

    .. todo::

        * :meth:`start_and_pause` 나 :meth:`monitor` 메소드의 용례와 이름이 부정확하며 서로간의 호출 순서가 존재한다.
    """

    _FILE_FORMATTER: ClassVar[ColoredFormatter] = ColoredFormatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] (%(funcName)s:%(lineno)d in %(filename)s) $ %(message)s')

    _bench_config: BenchConfig
    _identifier: str
    _monitors: Tuple[_MON_T, ...]
    _constraints: Tuple[BaseConstraint, ...]
    _pipeline: BasePipeline
    _log_path: Path
    _context_variable: Context

    @classmethod
    def of(cls, context: Context) -> BaseBenchmark:
        # noinspection PyProtectedMember
        for c, v in context._variable_dict.items():
            if issubclass(c, cls):
                return v

        raise BenchNotFoundError('Context variable should have exactly one Benchmark')

    @classmethod
    def _waits(cls, iterable: Iterable[Union[Future, Coroutine]]) -> Future[Tuple[Set[Future], Set[Future]]]:
        return asyncio.wait(tuple(iterable))

    def __new__(cls: Type[BaseBenchmark],
                bench_config: BenchConfig,
                constraints: Tuple[BaseConstraint, ...],
                monitors: Tuple[_MON_T, ...],
                pipeline: BasePipeline,
                privilege_config: PrivilegeConfig) -> BaseBenchmark:
        obj: BaseBenchmark = super().__new__(cls)

        obj._bench_config = bench_config
        obj._identifier = bench_config.identifier

        obj._monitors = monitors
        obj._constraints = constraints
        obj._pipeline = pipeline
        obj._context_variable = Context()

        # setup for logger
        obj._log_path = bench_config.workspace / 'logs' / f'{bench_config.identifier}.log'

        return obj

    async def start_and_pause(self, silent: bool = False) -> None:
        """
        벤치마크를 실행 하였다가, 실제로 벤치마크가 실행되어 프로세스가 생성되면 멈춘다.
        벤치마크를 실행하기 전에 :mod:`제약 <benchmon.benchmark.constraints>` 나 logger 등을 초기화 한다.

        .. note::
            * 한번 :meth:`start_and_pause` 를 통해 실행되었다가 정상 종료된 벤치마크의 경우,
              다시 한번 :meth:`start_and_pause` 를 통해 재활용할 수 있도록 구현 되어야 한다.

        :param silent: ``True`` 일 경우 화면에 출력되는 로그를 없앤다.
        :type silent: bool
        """
        self._remove_logger_handlers()

        # setup for loggers
        logger = logging.getLogger(self._identifier)

        privilege_cfg = PrivilegeConfig.of(self._context_variable).result

        with drop_privilege(privilege_cfg.user, privilege_cfg.group):
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

            fh = logging.FileHandler(self._log_path, mode='w')
            fh.setFormatter(BaseBenchmark._FILE_FORMATTER)
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
                await self._waits(con.on_init(self._context_variable) for con in self._constraints)
                logger.debug('Constraints are initialized')

            await self._pipeline.on_init(self._context_variable)
            logger.debug('Pipe is initialized')

            logger.info('Starting benchmark...')
            await self._start(self._context_variable)
            logger.info(f'The benchmark has started. pid : {self.pid}')

            logger.debug('Pausing benchmark...')
            self.pause()

        except asyncio.CancelledError:
            logger.debug(f'The task cancelled')
            if self.is_running:
                await self.kill()

            await self._destroy()

        except Exception as e:
            logger.critical(f'The following errors occurred during startup : {e}', e)
            if self.is_running:
                await self.kill()

            await self._destroy()

    async def monitor(self) -> None:
        """
        이 객체가 이미 실행된 후에 등록된 모니터로부터 벤치마크의 모니터링을 시작한다.
        """
        logger = logging.getLogger(self._identifier)
        logger.info('Start monitoring...')

        monitoring_tasks: Optional[asyncio.Task] = None

        # noinspection PyBroadException
        try:
            if len(self._constraints) is not 0:
                logger.debug('Initializing constraints...')
                await self._waits(con.on_start(self._context_variable) for con in self._constraints)
                logger.debug('Initializing of constraints are done')
            else:
                logger.debug('Skips initialization of constraints because there are no registered constraints')

            logger.debug('Initializing monitors...')
            await self._waits(mon.on_init(self._context_variable) for mon in self._monitors)
            logger.debug('Initializing of monitors are done')

            logger.debug('Starting monitoring...')
            monitoring_tasks = asyncio.create_task(self._waits(
                    mon.monitor(self._context_variable) for mon in self._monitors)
            )

            logger.debug('Wait for benchmark or monitors to finish')
            await asyncio.wait((self.join(), monitoring_tasks),
                               return_when=asyncio.FIRST_COMPLETED)

            if self.is_running:
                logger.debug('Monitoring is complete first. Wait for the benchmark to finish.')
                await self.join()
            else:
                logger.debug('The benchmark was completed first. Stopping monitor...')
                await self._waits(mon.stop() for mon in self._monitors)
                logger.debug('Waiting for monitors to finish...')
                await monitoring_tasks
                logger.debug('Monitors are complete')

            logger.info('The benchmark has been successfully completed.')

        except asyncio.CancelledError:
            logger.info('Monitoring has been canceled.')

            if self.is_running:
                logger.debug('Attempt to force termination of benchmark...')
                await self.kill()
                logger.debug('Benchmark has been aborted')

            if monitoring_tasks is not None and not monitoring_tasks.done():
                logger.debug('Stopping monitor...')
                await self._waits(mon.stop() for mon in self._monitors)
                logger.debug('Waiting for monitors to finish...')
                await monitoring_tasks
                logger.debug('Monitors are complete')

        except Exception as e:
            logger.critical(f'The following errors occurred during monitoring : {e}', e)

            if self.is_running:
                logger.debug('Attempt to force termination of benchmark due to error...')
                await self.kill()
                logger.debug('Benchmark has been aborted')

            if monitoring_tasks is not None and not monitoring_tasks.done():
                logger.debug('Stopping monitor...')
                await self._waits(mon.stop() for mon in self._monitors)
                logger.debug('Waiting for monitors to finish...')
                await monitoring_tasks
                logger.debug('Monitors are complete')

        finally:
            logger.info('The benchmark is ended.')

            # destroy monitors
            logger.debug('Deinitializing monitors...')
            await self._waits(mon.on_end(self._context_variable) for mon in self._monitors)
            logger.debug('Deinitialization of monitors are finished.')
            logger.debug('Destroying monitors...')
            await self._waits(mon.on_destroy(self._context_variable) for mon in self._monitors)
            logger.debug('Monitor destruction is complete.')

            await self._destroy()

    async def _destroy(self) -> None:
        logger = logging.getLogger(self._identifier)

        # destroy constraints
        if len(self._constraints) is not 0:
            logger.debug('Destroying constraints...')
            await self._waits(con.on_destroy(self._context_variable) for con in self._constraints)
            logger.debug('Constraint destruction is complete.')
        else:
            logger.debug('Skips destruction of constraints because there are no registered constraints')

        # destroy pipeline
        logger.debug('Deinitializing pipeline...')
        await self._pipeline.on_end(self._context_variable)
        logger.debug('Deinitialization of pipeline is finished.')
        logger.debug('Destroying pipeline...')
        await self._pipeline.on_destroy(self._context_variable)
        logger.debug('Pipeline destruction is complete.')

        self._remove_logger_handlers()

    @abstractmethod
    def pause(self) -> None:
        """
        벤치마크를 일시 정지한다.
        지원하지 않는 벤치마크 종류가 있을 수 있다.
        """
        pass

    @abstractmethod
    def resume(self) -> None:
        """
        벤치마크를 재시작한다.
        지원하지 않는 벤치마크 종류가 있을 수 있다.
        """
        pass

    @abstractmethod
    async def join(self) -> None:
        """ 벤치마크가 실행이 종료될 때 까지 이 메소드의 호출자의 실행을 멈춘다. """
        pass

    @abstractmethod
    async def _start(self, context: Context) -> None:
        """ 벤치마크별로 실제 벤치마크의 실행 방법을 서술한다. """
        pass

    @abstractmethod
    async def kill(self) -> None:
        """ 벤치마크의 실행을 멈추고 프로세스를 죽인다. """
        pass

    def _remove_logger_handlers(self) -> None:
        logger = logging.getLogger(self._identifier)

        for handler in tuple(logger.handlers):  # type: logging.Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    @property
    def identifier(self) -> str:
        """
        다른 벤치마크들과 이 벤치마크를 구분할 수 있는 유일한 문자열을 반환한다.

        :return: 다른 벤치마크들과 이 벤치마크를 구분할 수 있는 유일한 문자열
        :rtype: str
        """
        return self._identifier

    @property
    @abstractmethod
    def group_name(self) -> str:
        """
        cgroup이나 resctrl 등에서 쓰일 유니크한 문자열

        :return: cgroup이나 resctrl 등에서 쓰일 유니크한 문자열
        :rtype: str
        """
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """
        벤치마크 프로세스가 실제로 실행중인지를 반환

        :return: 벤치마크 프로세스의 실제 실행 여부
        :rtype: bool
        """
        pass

    @property
    @abstractmethod
    def pid(self) -> Optional[int]:
        """
        벤치마크 프로세스의 PID를 반환한다.

        :return: 벤치마크 프로세스의 PID. 아직 PID가 없다면 ``None``.
        :rtype: typing.Optional[int]
        """
        pass

    @property
    def bench_config(self) -> BenchConfig:
        return self._bench_config

    @abstractmethod
    def all_child_tid(self) -> Tuple[int, ...]:
        pass
