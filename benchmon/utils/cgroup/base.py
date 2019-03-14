# coding: UTF-8

import getpass
import grp
import os
from abc import ABCMeta
from pathlib import Path
from typing import ClassVar, Iterable

from ..asyncio_subprocess import check_run


class BaseCGroup(metaclass=ABCMeta):
    """
    기본적으로 모든 cgroup subsystem들이 공통으로 사용 가능한 기능들을 묶어놓은 클래스.

    .. note::
        * 내부적으로는 `cgcreate`, `cgm` 과 같은 shell command 들을 사용한다.

    .. todo::
        * command parameter들의 validation check
    """
    MOUNT_POINT: ClassVar[Path] = Path('/sys/fs/cgroup')
    CONTROLLER_NAME: ClassVar[str]

    _name: str

    def __init__(self, group_name: str) -> None:
        """
        `group_name` 을 이름으로하는 group을 handle하는 객체를 생성한다.

        실제로 group이 바로 생성되지는 않으며, :meth:`create_group` 를 호출해야 생성된다.

        :param group_name: 그룹의 이름
        :type group_name: str
        """
        super().__init__()

        self._name = group_name

    @classmethod
    def absolute_path(cls) -> Path:
        """
        자신의 클래스가 대표하는 subsystem이 Linux의 sysfs에서 실제로 위치한 경로를 반환한다

        :return: 자신의 subsystem이 sysfs에 실제로 위치한 경로
        :rtype: pathlib.Path
        """
        return cls.MOUNT_POINT / cls.CONTROLLER_NAME

    @property
    def identifier(self) -> str:
        """
        해당 객체가 대표하는 group의 ID (`subsystem`:`group_name` 형식)

        :return: 그룹의 ID
        :rtype: str
        """
        return f'{self.CONTROLLER_NAME}:{self._name}'

    async def create_group(self) -> None:
        """
        지정한 그룹 이름으로 group을 생성한다.

        그룹의 소유권은 현재 shell의 owner와 group으로 지정되며, `root` 권한이 필요하다.
        """
        uname: str = getpass.getuser()
        gid: int = os.getegid()
        gname: str = grp.getgrgid(gid).gr_name

        await check_run('cgcreate', '-a', f'{uname}:{gname}', '-d', '755', '-f', '644',
                        '-t', f'{uname}:{gname}', '-s', '644', '-g', self.identifier)

    async def chown(self, uid: int, gid: int) -> None:
        """
        해당 그룹의 소유권을 변경한다.

        :param uid: 새로운 owner의 user id
        :type uid: int
        :param gid: 새로운 group의 group id
        :type gid: int
        """
        await check_run('cgm', 'chown', self.CONTROLLER_NAME, self._name, str(uid), str(gid))

    async def chmod(self, mod: int) -> None:
        """
        해당 그룹 폴더의 권한을 변경한다

        :param mod: 변경할 권한 값
        :type mod: int
        """
        # TODO: validation of `mod`
        await check_run('cgm', 'chmod', self.CONTROLLER_NAME, self._name, str(mod))

    async def chmodfile(self, file: str, mod: int) -> None:
        """
        해당 그룹 안에있는 특정 파일의 권한을 변경한다

        :param file: 권한을 변경할 파일 이름
        :type file: str
        :param mod: 변경할 권한 값
        :type mod: int
        """
        # TODO: validation of `mod`
        await check_run('cgm', 'chmodfile', self.CONTROLLER_NAME, self._name, file, str(mod))

    @property
    def name(self) -> str:
        """
        group 이름을 반환한다.

        :return: group 이름
        :rtype: str
        """
        return self._name

    async def rename(self, new_name: str) -> None:
        """
        group 이름을 변경한다.

        :param new_name: 새로운 group의 이름
        :rtype: str
        """
        (self.absolute_path() / self._name).rename(self.absolute_path() / new_name)

        self._name = new_name

    async def add_tasks(self, pids: Iterable[int]) -> None:
        """
        `pids` 들을 해당 그룹에 추가한다

        :param pids: group에 추가할 pid들
        :rtype: typing.Iterable[int]
        """
        await check_run('cgclassify', '-g', self.identifier, '--sticky', *map(str, pids))

    async def delete(self) -> None:
        """ 해당 그룹을 삭제한다. """
        await check_run('cgdelete', '-r', '-g', self.identifier)
