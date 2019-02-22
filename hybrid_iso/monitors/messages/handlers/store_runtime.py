# coding: UTF-8

import json
from pathlib import Path
from typing import Dict, Optional

from benchmon import Context
from benchmon.benchmark import BaseBenchmark
from benchmon.configs.containers import BenchConfig
from benchmon.monitors import RuntimeMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler


class StoreRuntime(BaseHandler):
    _result_path: Path

    async def on_init(self, context: Context) -> None:
        workspace: Path = BenchConfig.of(context).workspace / 'monitored'
        self._result_path = workspace / 'runtime.json'

        if self._result_path.is_file():
            self._result_path.unlink()
        elif self._result_path.is_dir():
            self._result_path.rmdir()

        self._result_path.write_text('{}')

    async def on_message(self, context: Context, message: PerBenchMessage) -> Optional[PerBenchMessage]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, RuntimeMonitor):
            return message

        # TODO: evaluation between open and aiofile_linux
        # FIXME: does not overwrite previous experiment results
        with self._result_path.open(mode='r+') as fp:
            content_str = fp.read()
            content: Dict[str, float] = json.loads(content_str)
            content[BaseBenchmark.of(context).identifier] = message.data

            fp.seek(0)
            fp.truncate()
            fp.write(json.dumps(content))

            return message
