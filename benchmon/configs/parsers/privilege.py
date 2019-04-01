# coding: UTF-8

import grp
import pwd
from dataclasses import Field, fields
from typing import Dict, Union

from .base import LocalReadParser
from .. import get_full_path, validate_and_load
from ..containers import Privilege, PrivilegeConfig

PrivilegeConfigJson = Dict[str, Union[int, str, Dict[str, Union[str, int]]]]


class PrivilegeParser(LocalReadParser[PrivilegeConfig]):
    """ :mod:`benchmon.configs` 폴더 안에있는 `privilege.json` 를 읽어 파싱한다. """

    def _parse(self) -> PrivilegeConfig:
        config: PrivilegeConfigJson = validate_and_load(get_full_path('privilege.json'))
        config: Dict[str, Privilege] = self._deduct_config(config)
        local_config: PrivilegeConfigJson = self._local_config.get('privilege', dict())
        local_config: Dict[str, Privilege] = self._deduct_config(local_config)

        merged: Dict[str, Privilege] = dict()
        for field in fields(PrivilegeConfig):  # type: Field
            merged[field.name] = local_config.get(field.name, config[field.name])

        return PrivilegeConfig(**merged)

    @classmethod
    def _deduct_config(cls, config: PrivilegeConfigJson) -> Dict[str, Privilege]:
        if 'user' in config and 'group' in config:
            return dict(
                    (field.name, cls._parse_config(config))
                    for field in fields(PrivilegeConfig)
            )
        else:
            ret: Dict[str, Privilege] = dict()

            for field in fields(PrivilegeConfig):  # type: Field
                if field.name in config:
                    ret[field.name] = cls._parse_config(config[field.name])
            return ret

    @classmethod
    def _parse_config(cls, config: Dict[str, Union[str, int]]) -> Privilege:
        if isinstance(config['user'], str):
            config['user'] = pwd.getpwnam(config['user']).pw_uid

        if 'group' not in config:
            config['group'] = pwd.getpwuid(config['user']).pw_gid
        elif isinstance(config['group'], str):
            config['group'] = grp.getgrnam(config['group']).gr_gid

        return Privilege(config['user'], config['group'])
