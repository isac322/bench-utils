# coding: UTF-8

import subprocess
from pathlib import Path
from typing import Iterable, Set


class DVFS:
    MIN = int(Path('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq').read_text())
    STEP = 100000
    MAX = int(Path('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq').read_text())

    @staticmethod
    def set_freq(freq: int, cores: Iterable[int]) -> None:
        for core in cores:
            subprocess.run(args=('sudo', 'tee', f'/sys/devices/system/cpu/cpu{core}/cpufreq/scaling_max_freq'),
                           check=True, input=f'{freq}\n', encoding='ASCII', stdout=subprocess.DEVNULL)

    @staticmethod
    def convert_to_set(hyphen_str: str) -> Set[int]:
        ret = set()

        for elem in hyphen_str.split(','):
            group = tuple(map(int, elem.split('-')))

            if len(group) is 1:
                ret.add(group[0])
            elif len(group) is 2:
                ret.update(range(group[0], group[1] + 1))

        return ret
