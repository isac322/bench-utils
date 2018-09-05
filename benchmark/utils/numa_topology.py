from pathlib import Path
from typing import Dict, List, Tuple

import aiofiles


class NumaTopology:
    BASE_PATH = '/sys/devices/system/node'

    @staticmethod
    async def _get_node_topo() -> List[int]:
        base_path = Path(NumaTopology.BASE_PATH)
        online_path = base_path / 'online'
        async with aiofiles.open(online_path) as fp:
            line: str = await fp.readline()
            node_list = [int(num) for num in line.split('-')]
        return node_list

    @staticmethod
    async def _get_cpu_topo(node_list: List[int]) -> Dict[int, List[List[int]]]:
        base_path = Path(NumaTopology.BASE_PATH)
        cpu_topo: Dict[int, List[List[int]]] = dict()

        for num in node_list:
            cpulist_path = base_path / f'node{num}/cpulist'

            async with aiofiles.open(cpulist_path) as fp:
                line: str = await fp.readline()
                cpu_ranges: List[List[str]] = [cpus.split('-') for cpus in line.split(',')]
                int_cpu_ranges: List[List[int]] = list()
                for cpu_range in cpu_ranges:
                    int_cpu_range = [int(cpuid) for cpuid in cpu_range]
                    int_cpu_ranges.append(int_cpu_range)
                cpu_topo[num] = int_cpu_ranges
        return cpu_topo

    @staticmethod
    async def _get_mem_topo() -> List[int]:
        base_path = Path(NumaTopology.BASE_PATH)
        has_memory_path = base_path / 'has_memory'

        async with aiofiles.open(has_memory_path) as fp:
            line: str = await fp.readline()
            mem_list = line.split('-')
            mem_topo = [int(num) for num in mem_list]

            # TODO: mem_topo can be enhanced by using real numa memory access latency

        return mem_topo

    @staticmethod
    async def get_numa_info() -> Tuple[Dict[int, List[List[int]]], List[int]]:
        node_list = await NumaTopology._get_node_topo()
        cpu_topo = await NumaTopology._get_cpu_topo(node_list)
        mem_topo = await NumaTopology._get_mem_topo()
        return cpu_topo, mem_topo
