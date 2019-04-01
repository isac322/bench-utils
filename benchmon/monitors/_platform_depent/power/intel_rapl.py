# coding: UTF-8

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Dict, List, TYPE_CHECKING, Tuple, Union

from ... import BaseMonitor
from ...messages import SystemMessage
from ...pipelines import BasePipeline

if TYPE_CHECKING:
    from .... import Context

_ENERGY_FILE_NAME = 'energy_uj'
_MAX_ENERGY_VALUE_FILE_NAME = 'max_energy_range_uj'

T = Tuple[Dict[str, Union[str, int, Dict[str, int]]], ...]


class PowerMonitor(BaseMonitor[T]):
    _base_dir: ClassVar[Path] = Path('/sys/class/powercap/intel-rapl')

    _monitors: Dict[Path, Tuple[int, Dict[Path, int]]]

    def __init__(self) -> None:
        super().__init__()

        self._monitors = dict()

    async def on_init(self, context: Context) -> None:
        await super().on_init(context)

        while True:
            socket_id: int = len(self._monitors)
            socket_monitor: Path = PowerMonitor._base_dir / f'intel-rapl:{socket_id}'

            if socket_monitor.exists():
                with (socket_monitor / _ENERGY_FILE_NAME).open() as afp:
                    socket_power = int(afp.readline())

                socket_dict: Dict[Path, int] = dict()
                self._monitors[socket_monitor] = (socket_power, socket_dict)

                while True:
                    sub_id: int = len(socket_dict)
                    sub_monitor: Path = socket_monitor / f'intel-rapl:{socket_id}:{sub_id}'

                    if sub_monitor.exists():
                        with (sub_monitor / _ENERGY_FILE_NAME).open() as afp:
                            before = int(afp.readline())
                            socket_dict[sub_monitor] = before
                    else:
                        break
            else:
                break

    async def _monitor(self, context: Context) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def create_message(self, context: Context, data: T) -> SystemMessage[T]:
        return SystemMessage(data, self)

    async def on_end(self, context: Context) -> None:
        ret: List[Dict[str, Union[str, int, Dict[str, int]]]] = list()

        for socket_path, (prev_socket_power, socket) in self._monitors.items():
            with (socket_path / 'name').open() as name_fp, \
                    (socket_path / _ENERGY_FILE_NAME).open() as power_fp:
                sub_name = (name_fp.readline()).strip()
                after = int(power_fp.readline())

            if after > prev_socket_power:
                diff = after - prev_socket_power
            else:
                with (socket_path / _MAX_ENERGY_VALUE_FILE_NAME).open() as fp:
                    max_value = int(fp.readline())
                    diff = max_value - prev_socket_power + after

            ret_dict: Dict[str, Union[str, int, Dict[str, int]]] = {
                'package_name': sub_name,
                'power': diff,
                'domains': dict()
            }

            for path, before in socket.items():
                with (path / _ENERGY_FILE_NAME).open() as energy_fp, \
                        (path / 'name').open() as name_fp:
                    after = int(energy_fp.readline())
                    name = name_fp.readline().strip()

                    if after > prev_socket_power:
                        diff = after - before
                    else:
                        with (path / _MAX_ENERGY_VALUE_FILE_NAME).open() as fp:
                            max_value = int(fp.readline())
                            diff = max_value - before + after

                    ret_dict['domains'][name] = diff

            ret.append(ret_dict)

        msg = await self.create_message(context, tuple(ret))
        await BasePipeline.of(context).on_message(context, msg)
