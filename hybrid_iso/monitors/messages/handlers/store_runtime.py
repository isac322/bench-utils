# coding: UTF-8

import json
from pathlib import Path
from typing import Dict, Optional

import aiofiles

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
            async with aiofiles.open(str(result_path), mode='w') as afp:
                await afp.write(json.dumps({benchmark.identifier: message.data}))

                return message

        # FIXME: does not overwrite previous experiment results
        async with aiofiles.open(str(result_path), mode='r+') as afp:
            content_str = await afp.read()
            content: Dict[str, float] = json.loads(content_str)
            content[benchmark.identifier] = message.data

            await afp.seek(0)
            await afp.truncate()
            await afp.write(json.dumps(content))

            return message
