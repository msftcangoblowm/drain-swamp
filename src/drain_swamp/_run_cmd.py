"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Wrapper for :py:func:`subprocess.run` calls. Blocking and not multiprocessing

.. py:data:: __all__
   :type: tuple[str]
   :value: ("run_cmd",)

   Module exports

.. seealso::

   :py:mod:`drain_swamp._safe_path` contains path handling helper functions
   for dealing with:

   - getting absolute path to executable

   - fixing relative path

   - joinpath

"""

import os
import shlex
import subprocess
from collections.abc import Sequence
from pathlib import (
    Path,
    PurePath,
)

__all__ = ("run_cmd",)


def run_cmd(cmd, cwd=None, env=None):
    """Run cmd in subprocess, capture both stdout and stderr

    :param cmd: command to run in a subprocess
    :type cmd: collections.abc.Sequence[str]
    :param cwd: Default None
    :type cwd: pathlib.Path | None
    :param env: Default None. Expecting an :py:class:`os._Environ`
    :type env: typing.Any | None
    :returns: log messages, exception messages, return code, subprocess failure message
    :rtype: tuple[str | None, str | None, int | None, str | None]
    :raises:

        - :py:exc:`TypeError` -- Unsupported type for 1st arg cmd

    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd, Sequence):
        cmd = [os.fspath(x) for x in cmd]
    else:
        msg_warn = f"expected 1st param cmd to be a Sequence got {type(cmd)}"
        raise TypeError(msg_warn)

    if cwd is None or not issubclass(type(cwd), PurePath):
        path_cwd = Path.cwd()
    else:  # pragma: no cover
        path_cwd = cwd

    is_not_env = env is None or not isinstance(env, os._Environ)
    if is_not_env:
        opt_env = None
    else:  # pragma: no cover
        opt_env = env

    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=path_cwd,
            env=opt_env,
            text=True,
        )
    except OSError as e:
        # e.g. cmd=("bin/true",)
        str_err = str(f"{e.strerror} {e.filename}")
        ret = (None, None, None, str_err)
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as e:  # pragma: no cover
        """setuptools-scm requires at least one commit. Could not get
        semantic version"""
        # DO NOT USE proc.stdout, differing meaning
        str_err = str(e.stderr)
        str_out = None
        exit_code = None
        ret = (str_out, None, exit_code, str_err)
    else:
        # warning level log messages bleed to stdout
        str_out = proc.stdout
        str_err = proc.stderr
        is_empty_stdout = str_out is None or len(str_out.rstrip()) == 0
        is_empty_stderr = str_err is None or len(str_err.rstrip()) == 0

        if is_empty_stdout:
            str_out = None
        else:
            str_out = str_out.rstrip()

        # Exception details written to stderr
        if is_empty_stderr:
            str_err = None
        else:
            str_err = str_err.rstrip()

        # str_out is only Warning level log messages
        ret = (str_out, str_err, proc.returncode, None)

    return ret
