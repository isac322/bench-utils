# coding: UTF-8

import asyncio
from subprocess import CalledProcessError


# noinspection PyShadowingBuiltins
async def check_output(program: str, *args, input: bytes = None, **kwargs) -> str:
    if input is not None:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = asyncio.subprocess.PIPE

    proc = await asyncio.create_subprocess_exec(program, *args,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE, **kwargs)
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
