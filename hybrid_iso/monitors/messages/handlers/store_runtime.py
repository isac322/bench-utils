# coding: UTF-8

import json
from pathlib import Path
from typing import Dict, Optional

from benchmon.monitors import RuntimeMonitor
from benchmon.monitors.messages import PerBenchMessage
from benchmon.monitors.messages.handlers import BaseHandler


class StoreRuntime(BaseHandler):
    async def on_message(self, message: PerBenchMessage) -> Optional[PerBenchMessage]:
        if not isinstance(message, PerBenchMessage) or not isinstance(message.source, RuntimeMonitor):
            return message

        monitor: RuntimeMonitor = message.source
        benchmark = monitor._benchmark
        workspace: Path = benchmark._bench_config.workspace / 'monitored'
        result_path: Path = workspace / 'runtime.json'

        if not result_path.is_file():
            # TODO: evaluation between open and aiofile_linux
            with result_path.open(mode='w') as fp:
                fp.write(json.dumps({benchmark.identifier: message.data}))
                return message

        # TODO: evaluation between open and aiofile_linux
        # FIXME: does not overwrite previous experiment results
        with result_path.open(mode='r+') as fp:
            content_str = fp.read()
            content: Dict[str, float] = json.loads(content_str)
            content[benchmark.identifier] = message.data

            fp.seek(0)
            fp.truncate()
            fp.write(json.dumps(content))

            return message
