# coding: UTF-8

import asyncio
from subprocess import CalledProcessError
from typing import Union


# noinspection PyShadowingBuiltins
async def check_output(program: str, *args, input: bytes = None,
                       stderr: int = asyncio.subprocess.PIPE, **kwargs) -> Union[bytes, str]:
    if input is not None:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = asyncio.subprocess.PIPE

    proc = await asyncio.create_subprocess_exec(program, stdout=asyncio.subprocess.PIPE, stderr=stderr, *args, **kwargs)
    out, err = await proc.communicate(input)

    if proc.returncode:
        raise CalledProcessError(proc.returncode, (program, *args), output=out, stderr=err)

    return out


# noinspection PyShadowingBuiltins
async def check_run(program: str, *args, input: bytes = None, **kwargs) -> None:
    if input is not None:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = asyncio.subprocess.PIPE

    proc = await asyncio.create_subprocess_exec(program, *args, **kwargs)
    await proc.communicate(input)
