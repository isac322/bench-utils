# coding: UTF-8

import contextlib
import os


@contextlib.contextmanager
def drop_privilege(target_uid: int, target_gid: int):
    should_modify_gid = target_gid is not 0 and target_gid != os.getegid()
    should_modify_uid = target_uid is not 0 and target_uid != os.geteuid()

    if should_modify_gid:
        os.setegid(target_gid)
    if should_modify_uid:
        os.seteuid(target_uid)

    yield

    if should_modify_gid:
        os.setegid(0)
    if should_modify_uid:
        os.seteuid(0)
