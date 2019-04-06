# coding: UTF-8

from __future__ import annotations

import json
from typing import Dict, Optional, TYPE_CHECKING, TypeVar

from benchmon.benchmark import BaseBenchmark
from benchmon.configs.containers import PrivilegeConfig
from benchmon.monitors import RuntimeMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler
from benchmon.utils.privilege import drop_privilege

if TYPE_CHECKING:
    from pathlib import Path

    from benchmon import Context

_MT = TypeVar('_MT')


class StoreRuntime(BaseHandler):
    _result_path: Path

    async def on_init(self, context: Context) -> None:
        benchmark = BaseBenchmark.of(context)
        workspace: Path = benchmark.bench_config.workspace / 'monitored'
        self._result_path = workspace / 'runtime.json'

        privilege_cfg = PrivilegeConfig.of(context).result
        with drop_privilege(privilege_cfg.user, privilege_cfg.group):
            if self._result_path.is_file():
                self._result_path.unlink()
            elif self._result_path.is_dir():
                self._result_path.rmdir()

            self._result_path.parent.mkdir(exist_ok=True, parents=True)
            self._result_path.write_text('{}')

    async def on_message(self, context: Context, message: PerBenchMessage[_MT]) -> Optional[PerBenchMessage[_MT]]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, RuntimeMonitor):
            return message

        privilege_cfg = PrivilegeConfig.of(context).result
        with drop_privilege(privilege_cfg.user, privilege_cfg.group):
            with self._result_path.open(mode='r+') as fp:
                content: Dict[str, float] = json.load(fp)
                content[BaseBenchmark.of(context).identifier] = message.data

                fp.seek(0)
                fp.truncate()
                fp.write(json.dumps(content))

                return message
