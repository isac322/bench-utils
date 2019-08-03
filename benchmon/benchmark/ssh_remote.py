# coding: UTF-8

from __future__ import annotations

import logging
import signal
from abc import ABC
from typing import Optional, TYPE_CHECKING, Tuple, TypeVar

from .base import BaseBenchmark
from ..configs.containers import SSHConfig

if TYPE_CHECKING:
    from asyncssh import SSHClientConnection, SSHClientProcess

    from .constraints import BaseConstraint
    from .. import Context
    from ..monitors import BaseMonitor
    from ..monitors.pipelines import BasePipeline

    _CST_T = TypeVar('_CST_T', bound=BaseConstraint)
    _MON_T = TypeVar('_MON_T', bound=BaseMonitor)

_CFG_T = TypeVar('_CFG_T', bound=SSHConfig)


class SSHBenchmark(BaseBenchmark[_CFG_T], ABC):
    __slots__ = ('_ssh_conn', '_tunnel_conn')

    _tunnel_conn: Optional[SSHClientConnection]
    _ssh_conn: SSHClientConnection
    _ssh_proc: Optional[SSHClientProcess]

    @classmethod
    def of(cls, context: Context) -> Optional[SSHBenchmark]:
        # noinspection PyProtectedMember
        for c, v in context._variable_dict.items():
            if issubclass(c, cls):
                return v

        return None

    def __init__(self,
                 ssh_config: _CFG_T,
                 constraints: Tuple[_CST_T, ...],
                 monitors: Tuple[_MON_T, ...],
                 pipeline: BasePipeline,
                 tunnel_conn: Optional[SSHClientConnection],
                 ssh_conn: SSHClientConnection) -> None:
        super().__init__(ssh_config, constraints, monitors, pipeline)

        self._tunnel_conn = tunnel_conn
        self._ssh_conn = ssh_conn
        self._ssh_proc = None

    def __del__(self) -> None:
        if self.is_running:
            self._ssh_proc.kill()
            self._ssh_proc.close()

        self._ssh_conn.close()

        if self._tunnel_conn:
            self._tunnel_conn.close()

    def pause(self) -> None:
        super().pause()

        self._ssh_proc.channel.send_signal(signal.SIGSTOP)

    def resume(self) -> None:
        super().resume()

        self._ssh_proc.channel.send_signal(signal.SIGCONT)

    async def join(self) -> None:
        await super().join()

        await self._ssh_proc.wait()

    async def _start(self, context: Context) -> None:
        self._ssh_proc = await self._ssh_conn.create_process(self._bench_config.command)

    async def kill(self) -> None:
        await super().kill()

        logger = logging.getLogger(self._identifier)

        if self.is_running:
            self._ssh_proc.kill()
            self._ssh_proc.close()
        else:
            logger.debug('Process already killed.')

    @property
    def is_running(self) -> bool:
        return self._ssh_proc.returncode is None
