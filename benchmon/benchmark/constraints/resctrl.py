# coding: UTF-8

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING, Tuple, Type

from .base import BaseConstraint
from .base_builder import BaseBuilder
from ...utils import ResCtrl

if TYPE_CHECKING:
    from ..base import BaseBenchmark


class ResCtrlConstraint(BaseConstraint):
    """
    :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>` 의 실행 직후에 해당 벤치마크가 사용할 수 있는 최대 LLC를
    resctrl를 통해 입력받은 값으로 제한하며, 벤치마크의 실행이 종료될 경우 그 resctrl 그룹을 삭제한다.
    """
    _masks: Tuple[str, ...]
    _group: ResCtrl

    def __new__(cls: Type[ResCtrlConstraint], bench: BaseBenchmark, masks: Tuple[str, ...]) -> ResCtrlConstraint:
        """
        .. TODO: `masks` 의 타입을 Iterable로 변경
        :param bench: 이 constraint가 붙여질 :class:`벤치마크 <bench_toolbox.benchmark.base.BaseBenchmark>`
        :type bench: bench_toolbox.benchmark.base.BaseBenchmark
        :param masks: CPU 소켓별로 할당할 LLC mask
        :type masks: typing.Tuple[str, ...]
        """
        obj: ResCtrlConstraint = super().__new__(cls, bench)

        obj._masks = masks
        obj._group = ResCtrl()

        return obj

    def __init__(self, **kwargs) -> None:
        raise NotImplementedError('Use {0}.Builder to instantiate {0}'.format(self.__class__.__name__))

    async def on_start(self) -> None:
        self._group.group_name = self._benchmark.group_name

        await self._group.create_group()

        if len(self._masks) is not 0:
            await self._group.assign_llc(*self._masks)

        children = self._benchmark.all_child_tid()
        await self._group.add_tasks(children)

    async def on_destroy(self) -> None:
        try:
            await self._group.delete()
        except PermissionError:
            pass

    class Builder(BaseBuilder['ResCtrlConstraint']):
        """ :class:`~bench_toolbox.benchmark.constraints.resctrl.ResCtrlConstraint` 를 객체화하는 빌더 """
        _masks: Tuple[str, ...] = tuple()

        def __init__(self, masks: Iterable[str] = tuple()) -> None:
            """
            .. TODO: `masks` 의 타입을 Iterable로 변경
            :param masks: CPU 소켓별로 할당할 LLC mask
            :type masks: typing.Tuple[str, ...]
            """
            self._masks = masks

        def finalize(self, benchmark: BaseBenchmark) -> ResCtrlConstraint:
            return ResCtrlConstraint.__new__(ResCtrlConstraint, benchmark, self._masks)
