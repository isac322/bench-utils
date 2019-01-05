# coding: UTF-8

import asyncio
import re
from itertools import chain
from pathlib import Path
from typing import ClassVar, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple

import aiofiles
from aiofiles.base import AiofilesContextManager


def mask_to_bits(mask: str) -> int:
    """
    `CBM string <https://software.intel.com/en-us/articles/introduction-to-cache-allocation-technology>`_ 을 int로 변환

    :param mask: 변환할 CBM string
    :type mask: str
    :return: 변환된 CBM
    :rtype: int
    """
    cnt = 0
    num = int(mask, 16)
    while num is not 0:
        cnt += 1
        num >>= 1
    return cnt


def bits_to_mask(bits: int) -> str:
    """
    int로 된 CBM을 string으로 변환

    :param bits: 변환할 CBM
    :type bits: int
    :return: 변환된 CBM string
    :rtype: str
    """
    return f'{bits:x}'


async def _open_file_async(monitor_dict: MutableMapping[Path, AiofilesContextManager]) -> None:
    for file_path in monitor_dict:
        monitor_dict[file_path] = await aiofiles.open(file_path)


async def _read_file(path: Path, monitor: AiofilesContextManager) -> Tuple[str, int]:
    await monitor.seek(0)
    return path.name, int(await monitor.readline())


class ResCtrl:
    """
    리눅스에서 `/sys/fs/resctrl` 에 마운트 되는 Intel CAT과 관련된 API wrapper.

    .. note::
        * :meth:`read` 같은 메소드를 호출하기 이전에 딱 한번 :meth:`prepare_to_read` 으로 초기화 해줘야 한다.
        * 현재 `info/L3_MON/mon_features` 에 listing된 것들의 monitoring 기능과, CAT 기능을 지원함.
        * 모든 기능들은 파일 읽기 쓰기를 통해 진행되기 때문에, 잦은 호출은 큰 오버헤드를 가져올 수 있음

    .. todo::

        * 초기화를 담당하는 부분이 생성자와 :meth:`prepare_to_read` 로 나뉜 점, :meth:`group_name` setter로
          나중에 그룹 이름을 수정하는 점 등, 해당 클래스의 의미에 inconsistency가 존재한다.

            * 객체가 가리키고있는 그룹을 변경할 수 없게하고 (immutable. 아니면 그룹의 re-pointing이 아닌 renaming으로 기능 수정)
            * 객체 생성과 동시에 관련된 초기화를 한번에 수행 ('생성자' 라는 의미에 대한 consistency)

        * 오버헤드를 낮추기 위해 통신 방법을 File I/O에서 아래의 candidate중 하나로 변경해야할 듯

            * :mod:`aiofiles` 는 내부적으로 POSIX AIO를 사용하며, 이는 Linux glibc에서 내부적으로 thread pool을 사용함.
              (`Notes 참조 <https://linux.die.net/man/7/aio>`_)
              따라서 `Linux kernel AIO <http://lse.sourceforge.net/io/aio.html>`_ 를 사용하는 모듈을 새로 작성하여 사용
                * 하지만 사실상 결국 좀 더 빠른 File I/O일 뿐, 큰 오버헤드 감소는 기대하기 어려울 수도 있음

            * msr 등을 사용하여 manual하게 COS를 수정하는 C 혹은 Python 모듈을 작성하여 이용

                * File I/O를 전혀 사용하지 않기 때문에 큰 오버헤드 감소 예상
                * 하지만 H/W dependent 할 수도..?
                * 현재까지 경험에 의하면 root 권한 필요
    """
    MOUNT_POINT: ClassVar[Path] = Path('/sys/fs/resctrl')

    # FIXME: H/W support check before adjust config to benchmark
    if MOUNT_POINT.exists():
        FEATURES: ClassVar[Tuple[str, ...]] = tuple(
                (MOUNT_POINT / 'info' / 'L3_MON' / 'mon_features').read_text('ASCII').strip().split()
        )

        # filter L3 related monitors and sort by name (currently same as socket number)
        _MON_NAMES: ClassVar[Tuple[str, ...]] = tuple(sorted(
                map(
                        lambda x: x.name,
                        filter(
                                lambda m: re.match(r'mon_L3_(\d+)', m.name),
                                MOUNT_POINT.joinpath('mon_data').glob('mon_L3_*')
                        )
                )
        ))

        MAX_MASK: ClassVar[str] = MOUNT_POINT.joinpath('info/L3/cbm_mask').read_text(encoding='ASCII').strip()
        MAX_BITS: ClassVar[int] = mask_to_bits(MAX_MASK)
        MIN_BITS: ClassVar[int] = int((MOUNT_POINT / 'info' / 'L3' / 'min_cbm_bits').read_text())
        MIN_MASK: ClassVar[str] = bits_to_mask(MIN_BITS)

    _group_name: str
    _group_path: Path
    _prepare_read: bool = False
    # tuple of each feature monitors for each socket
    _monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...]

    def __init__(self) -> None:
        self.group_name = str()

    @property
    def group_name(self) -> str:
        """
        현재 이 객체가 가리키고있는 그룹의 이름

        :return: 그룹의 이름
        :rtype: str
        """
        return self._group_name

    @group_name.setter
    def group_name(self, new_name) -> None:
        """
        현재 이 객체가 가리키고있는 그룹을 `new_name` 으로 변경.

        .. note::
            * 기존에 이 객체가 가리키고있던 그룹의 이름을 바꾸는 것이 아닌, 다른 그룹을 가리키도록 함

        .. todo::

            * 이 클래스의 전체 설명에서 언급한 inconsistency 문제가 존재

        :param new_name: 새로 pointing 할 그룹의 이름
        :type new_name: str
        """
        self._group_name = new_name
        self._group_path = ResCtrl.MOUNT_POINT / new_name
        self._monitors: Tuple[Dict[Path, Optional[AiofilesContextManager]], ...] = tuple(
                dict.fromkeys(
                        self._group_path / 'mon_data' / mon_name / feature for feature in ResCtrl.FEATURES
                )
                for mon_name in ResCtrl._MON_NAMES
        )

    async def create_group(self) -> None:
        """현재 객체가 가리키고 있는 그룹이 실제로 존재하지 않는 그룹이라면, 그룹 생성"""
        proc = await asyncio.create_subprocess_exec('sudo', 'mkdir', '-p', str(self._group_path))
        await proc.communicate()

    async def prepare_to_read(self) -> None:
        """
        :meth:`read` 를 사용하기 전에 준비하는 메소드

        .. todo::

            * 이 클래스의 전체 설명에서 언급한 inconsistency 문제가 존재
        """
        if self._prepare_read:
            raise AssertionError('The ResCtrl object is already prepared to read.')

        self._prepare_read = True
        await asyncio.wait(tuple(map(_open_file_async, self._monitors)))

    async def add_task(self, pid: int) -> None:
        """
        `pid` 를 이 객체가 가리키는 그룹에 추가

        :param pid: 그룹에 추가할 pid
        :type pid: int
        """
        proc = await asyncio.create_subprocess_exec('sudo', 'tee', '-a', str(self._group_path / 'tasks'),
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.DEVNULL)
        await proc.communicate(str(pid).encode())

    async def add_tasks(self, pids: Iterable[int]) -> None:
        """
        `pids` 들을 이 객체가 가리키는 그룹에 모두 추가

        .. todo::

            * 내부적으로 :meth:`add_task` 를 여러번 호출하는데, 이 경우 파일 쓰기를 순차적으로 사용하기 때문에 큰 delay가 생김
              * 현재까지 Linux의 `/sys/fs/resctrl` 인터페이스를 통한 task 추가는 순차적으로 밖에 진행할 수 없음

        :param pids: 추가할 pid들
        :type pids: typing.Iterable[int]
        """
        for pid in pids:
            await self.add_task(pid)

    async def assign_llc(self, *masks: str) -> None:
        """
        `schemata` 에 `masks` 를 적음으로써 이 그룹의 LLC를 제한한다.

        `masks` 는 :meth:`gen_mask` 나 :func:`bits_to_mask` 를 통해 얻을 수 있다.

        .. note::
            * `masks` 가 가변길이 매개변수이기 때문에, 머신에 여러 LLC가 있다면 각 LLC에 대한 제한량을 차례대로 정할 수 있다.

        :param masks: 각 LLC에 적용할 CBMs string
        :type masks: typing.Tuple[str, ...]
        """
        masks = (f'{i}={m}' for i, m in enumerate(masks))
        proc = await asyncio.create_subprocess_exec('sudo', 'tee', str(self._group_path / 'schemata'),
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.DEVNULL)
        await proc.communicate(f'L3:{";".join(masks)}\n'.encode())

    @staticmethod
    def gen_mask(start: int, end: int = None) -> str:
        """
        MSB를 기준으로 `start` 번째 비트부터 `end` 비트까지 set된 CBM string을 만든다

        :param start: set할 비트들 구간의 시작 위치 (MSB 기준)
        :type start: int
        :param end: set할 비트들 구간의 마지막 위치 (MSB 기준)
        :type end: int
        :return: 만들어진 CBM string
        :rtype: str
        """
        if end is None or end > ResCtrl.MAX_BITS:
            end = ResCtrl.MAX_BITS

        if start < 0:
            raise ValueError('start must be greater than 0')

        return format(((1 << (end - start)) - 1) << (ResCtrl.MAX_BITS - end), 'x')

    async def read(self) -> Tuple[Mapping[str, int], ...]:
        """
        `info/L3_MON/mon_features` 에 listing된 것들을 monitoring하여 각 LLC마다 {`mon_feature`: `value`}의 dict로 반환

        .. note::
            * 내부적으로 File I/O를 사용하기 때문에 각 모니터링 값간에 약간의 시간차가 존재할 수 있다

        :return: 모니터링한 값
        :rtype: typing.Tuple[typing.Mapping[str, int], ...]
        """
        if not self._prepare_read:
            raise AssertionError('The ResCtrl object is not ready to read.')

        return tuple(
                map(dict,
                    await asyncio.gather(*(
                        # TODO: check map(_read_file, mons.items())
                        asyncio.gather(*(_read_file(k, v) for k, v in mons.items()))
                        for mons in self._monitors))
                    )
        )

    async def end_read(self) -> None:
        """:meth:`prepare_to_read` 를 통해 초기화한 것들을 돌려 놓음"""
        if not self._prepare_read:
            raise AssertionError('The ResCtrl object is not ready to read.')

        await asyncio.wait(tuple(
                chain(*(
                    (mon.close() for mon in mons.values())
                    for mons in self._monitors
                ))
        ))

    async def delete(self) -> None:
        """
        이 객체가 가리키고있던 그룹을 실제로 삭제함

        .. note::
            * root 권한이 필요함
        """
        if self._prepare_read:
            await self.end_read()

        if self._group_name is str():
            raise PermissionError('Can not remove root directory of resctrl')

        proc = await asyncio.create_subprocess_exec('sudo', 'rmdir', str(self._group_path))
        await proc.communicate()
