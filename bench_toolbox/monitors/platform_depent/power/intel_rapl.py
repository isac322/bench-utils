# coding: UTF-8

from __future__ import annotations

from pathlib import Path
from typing import Callable, ClassVar, Coroutine, Dict, List, Tuple, Type, Union

import aiofiles

from ...base import BaseMonitor
from ...base_builder import BaseBuilder
from ...messages.base import BaseMessage
from ...messages.system import SystemMessage

_ENERGY_FILE_NAME = 'energy_uj'
_MAX_ENERGY_VALUE_FILE_NAME = 'max_energy_range_uj'

T = Tuple[Dict[str, Union[str, int, Dict[str, int]]]]


class PowerMonitor(BaseMonitor[T]):
    _base_dir: ClassVar[Path] = Path('/sys/class/powercap/intel-rapl')

    _monitors: Dict[Path, Tuple[int, Dict[Path, int]]]

    def __new__(cls: Type[BaseMonitor],
                emitter: Callable[[BaseMessage[T]], Coroutine[None, None, None]]) -> PowerMonitor:
        obj: PowerMonitor = super().__new__(cls, emitter)
        obj._monitors = dict()
        return obj

    async def on_init(self) -> None:
        await super().on_init()

        while True:
            socket_id: int = len(self._monitors)
            socket_monitor: Path = PowerMonitor._base_dir / f'intel-rapl:{socket_id}'

            if socket_monitor.exists():
                async with aiofiles.open(str(socket_monitor / _ENERGY_FILE_NAME)) as afp:
                    socket_power = int(await afp.readline())

                socket_dict: Dict[Path, int] = dict()
                self._monitors[socket_monitor] = (socket_power, socket_dict)

                while True:
                    sub_id: int = len(socket_dict)
                    sub_monitor: Path = socket_monitor / f'intel-rapl:{socket_id}:{sub_id}'

                    if sub_monitor.exists():
                        async with aiofiles.open(str(sub_monitor / _ENERGY_FILE_NAME)) as afp:
                            before = int(await afp.readline())
                            socket_dict[sub_monitor] = before
                    else:
                        break
            else:
                break

    async def _monitor(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def create_message(self, data: T) -> SystemMessage[T]:
        return SystemMessage(data, self)

    async def on_end(self) -> None:
        ret: List[Dict[str, Union[str, int, Dict[str, int]]]] = list()

        for socket_path, (prev_socket_power, socket) in self._monitors.items():
            async with aiofiles.open(str(socket_path / 'name')) as name_fp, \
                    aiofiles.open(str(socket_path / _ENERGY_FILE_NAME)) as power_fp:
                sub_name = (await name_fp.readline()).strip()
                after = int(await power_fp.readline())

            if after > prev_socket_power:
                diff = after - prev_socket_power
            else:
                async with aiofiles.open(str(socket_path / _MAX_ENERGY_VALUE_FILE_NAME)) as afp:
                    max_value = int(await afp.readline())
                    diff = max_value - prev_socket_power + after

            ret_dict: Dict[str, Union[str, int, Dict[str, int]]] = {
                'package_name': sub_name,
                'power': diff,
                'domains': dict()
            }

            for path, before in socket.items():
                async with aiofiles.open(str(path / _ENERGY_FILE_NAME)) as energy_fp, \
                        aiofiles.open(str(path / 'name')) as name_fp:
                    after = int(await energy_fp.readline())
                    name = (await name_fp.readline()).strip()

                    if after > prev_socket_power:
                        diff = after - before
                    else:
                        async with aiofiles.open(str(path / _MAX_ENERGY_VALUE_FILE_NAME)) as afp:
                            max_value = int(await afp.readline())
                            diff = max_value - before + after

                    ret_dict['domains'][name] = diff

            ret.append(ret_dict)

        msg = await self.create_message(tuple(ret))
        await self._emitter(msg)

    class Builder(BaseBuilder['PowerMonitor']):
        def _finalize(self) -> PowerMonitor:
            return PowerMonitor.__new__(PowerMonitor, self._cur_emitter)
