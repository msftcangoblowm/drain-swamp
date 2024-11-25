"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Create ``.lock`` files. Calls :command:`pip-compile` multiple times
without coordination. Causing mostly resolvable mistakes.

``.shared.in`` files, being shared across **multiple** venv, presents
a situation where an intelligent human needs to step in and plan
how best to resolve the issue.

- if there are nudge pins could those be moved elsewhere?
- are there any dependency resolution conflicts caused?

KISS principle applies. Keep it simple

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Flag to turn on module level logging. Should be off in production

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("is_timeout", "lock_compile")

   Module exports

"""

import fileinput
import logging
import os
import re
import sys
from functools import singledispatch
from pathlib import (
    Path,
    PurePath,
)

from ._package_installed import is_package_installed
from ._run_cmd import run_cmd
from ._safe_path import (
    get_venv_python_abspath,
    resolve_path,
)
from .check_type import is_ok
from .constants import (
    SUFFIX_LOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_infile import InFiles
from .lock_util import replace_suffixes_last
from .pep518_venvs import get_reqs

is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.lock_compile")

__all__ = (
    "is_timeout",
    "lock_compile",
)


@singledispatch
def prepare_pairs(t_ins):
    """Fallback for unsupported data types without implementations

    Do not add type annotations. It's correct as-is.

    :raises:

       - :py:exc:`NotImplementedError` -- No implementation for 1st arg unsupported type

    """
    msg_warn = f"No implemenatation for type {t_ins}"
    raise NotImplementedError(msg_warn)


@prepare_pairs.register(tuple)
def _(t_ins: tuple[Path]):
    """Prepare (``.in`` ``.lock`` pairs) of only the direct requirements,
    not the support files.

    :param t_ins: Absolute path of the requirement ``.in`` file(s)
    :type t_ins: tuple[pathlib.Path]
    :returns: Yield .in .lock pairs. Absolute paths.
    :rtype: collections.abc.Generator[tuple[str, str], None, None]
    """
    for abspath_in in t_ins:
        abspath_locked = replace_suffixes_last(abspath_in, SUFFIX_LOCKED)
        yield str(abspath_in), str(abspath_locked)
    yield from ()


@prepare_pairs.register
def _(in_files: InFiles, path_cwd=None):
    """This would prepare (.in .lock pairs), not only for the reqs,
    but also the support files. Compiling the support files is not needed.

    But here is how to do that.

    :param in_files:

       Requirements. After resolution_loop, so contains both reqs and support files

    :type in_files: drain_swamp.lock_infile.InFiles
    :param path_cwd: cwd so can get the requirement file's absolute path
    :type path_cwd: pathlib.Path | None
    :returns: Yield .in .lock pairs. Absolute paths.
    :rtype: collections.abc.Generator[tuple[str, str], None, None]
    """
    assert path_cwd is not None and issubclass(type(path_cwd), PurePath)
    gen = in_files.zeroes
    for in_ in gen:
        abspath_in = in_.abspath(path_cwd)
        abspath_locked = replace_suffixes_last(abspath_in, SUFFIX_LOCKED)

        yield str(abspath_in), str(abspath_locked)
    yield from ()


def _postprocess_abspath_to_relpath(path_out, path_parent):
    """Within a lock file (contents), if an absolute path make relative
    by removing parent path

    To see the lock file format

    .. code-block:: shell

       pip-compile --dry-run docs/requirements.in

    :param path_out: Absolute path of the requirements file
    :type path_out: pathlib.Path
    :param path_parent: Absolute path to the parent folder of the requirements file
    :type path_parent: pathlib.Path
    """
    files = (path_out,)
    # py310 encoding="utf-8"
    with fileinput.input(files, inplace=True) as f:
        for line in f:
            is_lock_requirement_line = line.startswith("    # ")
            if is_lock_requirement_line:
                # process line
                line_modified = line.replace(f"{path_parent!s}/", "")
                sys.stdout.write(line_modified)
            else:  # pragma: no cover
                # do not modify line
                sys.stdout.write(line)


def _compile_one(
    in_abspath,
    lock_abspath,
    ep_path,
    path_cwd,
    venv_relpath,
    timeout=15,
):
    """Run subprocess to compile ``.in`` --> ``.lock``.

    Serial, it's what's for breakfast

    :param in_abspath: ``.in`` file absolute path
    :type in_abspath: str
    :param lock_abspath: output absolute path. Should have ``.lock`` last suffix
    :type lock_abspath: str
    :param ep_path: Absolute path to binary executable
    :type ep_path: str
    :param path_cwd: package base folder absolute Path
    :type path_cwd: pathlib.Path
    :param venv_relpath:

       From the venv relative path, get the Python interpreter absolute path
       and pass thru to pip.

    :type venv_relpath: str
    :param timeout: Default 15. Give ``pip --timeout`` in seconds
    :type timeout: typing.Any
    :returns:

       On success, Path to ``.lock`` file otherwise None. 2nd is error
       and exception details

    :rtype: tuple[pathlib.Path | None, None | str]
    """
    dotted_path = f"{g_app_name}.lock_inspect._compile_one"

    if timeout is None or not isinstance(timeout, int):
        timeout = 15
    else:  # pragma: no cover
        pass

    """pip-compile runs with Python interpreter A.
    pip runs against Python interpreter B.

    Do not know whether or not Python interpreter B is setup in venv
    relative path folder
    """
    try:
        venv_python_abspath = get_venv_python_abspath(path_cwd, venv_relpath)
    except NotADirectoryError:  # pragma: no cover
        # venv not setup with appropriate python interpreter version.
        # pip-compile results will be wrong, but **might** still run
        line_python = ""
        msg_warn = (
            f"venv not setup under folder, {venv_relpath} "
            "with the appropriate python interpreter version. "
            "Running pip-compile with current python executable. "
            "pip-compile results will be wrong, but might still run."
        )
        _logger.warning(msg_warn)
    else:  # pragma: no cover
        # venv found. Hopefully with the correct Python interpreter version
        is_file = (
            Path(venv_python_abspath).exists() and Path(venv_python_abspath).is_file()
        )
        if is_file:
            line_python = f"--pip-args='--python={venv_python_abspath!s}'"
        else:
            """Couldn't find Python interpreter, fallback to current one
            In tests, base folder is tmp_path, not path_cwd. Needs a
            *parent_dir* override param
            """
            line_python = ""

    cmd = (
        ep_path,
        "--allow-unsafe",
        "--no-header",
        "--resolver",
        "backtracking",
        "--pip-args='--isolated'",
        f"--pip-args='--timeout={timeout!s}'",
        f"{line_python}",
        "-o",
        lock_abspath,
        in_abspath,
    )

    if is_module_debug:  # pragma: no cover
        msg_info = f"{dotted_path} ({venv_relpath}) cmd: {cmd}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    t_ret = run_cmd(cmd, cwd=path_cwd)
    _, err, exit_code, exc = t_ret

    if exit_code != 0:  # pragma: no cover
        """timeout error message

        WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None,
        status=None)) after connection broken by 'NewConnectionError('
        <pip._vendor.urllib3.connection.HTTPSConnection object at 0x7fe86a05d670>:
        Failed to establish a new connection: [Errno -3] Temporary failure
        in name resolution')': /simple/pip-tools/

        Search for ``Failed to establish a new connection`` to detect timeouts
        """
        err = err.lstrip()
        if exit_code == 1 and "Failed to establish a new connection" in err:
            err = "timeout (15s)"
            err_details = err
        else:
            err_details = f"{err}{os.linesep}{exc}"
            msg_warn = (
                f"{dotted_path} ({venv_relpath}) {cmd!r} exit code "
                f"{exit_code} {err} {exc}"
            )
            _logger.warning(msg_warn)
    else:  # pragma: no cover
        err_details = None

    path_out = Path(lock_abspath)
    is_confirm = path_out.exists() and path_out.is_file()
    if is_confirm:
        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} ({venv_relpath}) yield: {path_out!s}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            msg_warn = f"{dotted_path} ({venv_relpath}) .lock created: {path_out!s}"
            _logger.warning(msg_warn)

        # abspath --> relpath
        _postprocess_abspath_to_relpath(path_out, path_cwd)

        ret = path_out, err_details
    else:
        """File not created. ``.in`` file contained errors that needs
        to be fixed. Log info adds context. Gives explanation about consequences
        """
        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{dotted_path} ({venv_relpath}) {in_abspath} malformed. "
                f"pip-compile did not create: {path_out!s}."
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass
        ret = None, err_details

    return ret


def lock_compile(loader, venv_relpath, timeout=15):
    """In a subprocess, call :command:`pip-compile` to create ``.lock`` files

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_relpath: venv relative path is a key. To choose a tools.venvs.req
    :type venv_relpath: str
    :param timeout: Default 15. Give ``pip --timeout`` in seconds
    :type timeout: typing.Any
    :returns: Generator of abs path to .lock files
    :rtype: tuple[tuple[str, ...], tuple[str, ...]]
    :raises:

       - :py:exc:`AssertionError` -- package pip-tools is not installed

    """
    dotted_path = f"{g_app_name}.lock_inspect.lock_compile"
    is_installed = is_package_installed("pip-tools")
    path_ep = resolve_path("pip-compile")
    assert is_installed is True and path_ep is not None
    ep_path = str(path_ep)

    if timeout is None or not isinstance(timeout, int):
        timeout = 15
    else:  # pragma: no cover
        pass

    # TODO: during testing, this is tmp_path, not package base folder
    if is_module_debug:  # pragma: no cover
        msg_info = f"{dotted_path} path_cwd (loader.project_base) {loader.project_base}"
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass
    path_cwd = loader.project_base

    compiled = []
    failures = []

    if is_ok(venv_relpath):
        # One
        venv_relpaths = [venv_relpath]
    else:
        # All
        venv_relpaths = loader.venv_relpaths

    for venv_relpath_tmp in venv_relpaths:
        try:
            t_abspath_in = get_reqs(loader, venv_path=venv_relpath_tmp)
        except (NotADirectoryError, ValueError, KeyError):
            """NotADirectoryError -- venv relative paths do not correspond
                                     to actual venv folders
            ValueError -- expecting [[tool.venvs]] field reqs to be a sequence
            KeyError -- No such venv found
            """
            raise
        except MissingRequirementsFoldersFiles:
            raise

        # t_ins, files = filter_by_venv_relpath(loader, venv_relpath_tmp)
        gen_pairs = prepare_pairs(t_abspath_in)
        pairs = list(gen_pairs)

        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} pairs {pairs!r}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        assert isinstance(ep_path, str)
        assert issubclass(type(path_cwd), PurePath)
        assert venv_relpath_tmp is not None or isinstance(venv_relpath_tmp, str)
        for in_abspath, lock_abspath in pairs:
            # Conforms to interface?
            assert isinstance(in_abspath, str)
            assert isinstance(lock_abspath, str)

            if is_module_debug:  # pragma: no cover
                msg_info = (
                    f"{dotted_path} (before _compile_one) cwd {path_cwd} "
                    f"binary {ep_path} {in_abspath} {lock_abspath}"
                )
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            optabspath_lock, err_details = _compile_one(
                in_abspath,
                lock_abspath,
                ep_path,
                path_cwd,
                venv_relpath_tmp,
                timeout=timeout,
            )
            # if timeout cannot add to compiled. If no timeout, maybe failures empty
            if optabspath_lock is None:  # pragma: no cover
                msg = f"venv {venv_relpath_tmp} {lock_abspath} {err_details}"
                failures.append(msg)
            else:  # pragma: no cover
                # Path
                msg = lock_abspath
                compiled.append(msg)

    return (tuple(compiled), tuple(failures))


def is_timeout(failures):
    """lock_compile returns both success and failures. Detect
    if the cause of the failure was timeout(s)

    :param failures: Sequence of verbose error message and traceback
    :type failures: tuple[str, ...]
    :returns: True if web (actually SSL) connection timeout occurred
    :rtype: bool
    """
    if len(failures) != 0:  # pragma: no cover
        failure_0 = failures[0]
        is_timeout = re.search("timeout.+s", failure_0)
    else:  # pragma: no cover
        is_timeout = False

    return is_timeout
