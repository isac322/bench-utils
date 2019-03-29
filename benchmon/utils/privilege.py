# coding: UTF-8

import contextlib
import os


@contextlib.contextmanager
def drop_privilege(target_uid: int, target_gid: int):
    backup_egid = os.getegid()
    should_modify_gid = target_gid != backup_egid
    backup_euid = os.geteuid()
    should_modify_uid = target_uid != backup_euid

    if should_modify_gid:
        os.setresgid(target_gid, target_gid, backup_egid)
    if should_modify_uid:
        os.setresuid(target_uid, target_uid, backup_euid)

    yield

    if should_modify_gid:
        os.setresgid(backup_egid, backup_egid, backup_egid)
    if should_modify_uid:
        os.setresuid(backup_euid, backup_euid, backup_euid)
