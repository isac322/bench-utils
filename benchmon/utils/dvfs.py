# coding: UTF-8

import asyncio
from typing import Iterable, Tuple

import aiofiles


async def set_max_freq(core_id: int, freq: int) -> None:
    proc = await asyncio.create_subprocess_exec(
            'sudo', 'tee', f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL)

    await proc.communicate(f'{freq}\n'.encode())


async def set_max_freqs(core_ids: Iterable[int], freq: int) -> None:
    await asyncio.wait(tuple(set_max_freq(core_id, freq) for core_id in core_ids))


async def read_max_freq(core_id) -> int:
    async with aiofiles.open(f'/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq') as afp:
        line: str = await afp.readline()
        return int(line)


async def read_max_freqs(core_ids: Iterable[int]) -> Tuple[int, ...]:
    return await asyncio.gather(*map(read_max_freq, core_ids))
