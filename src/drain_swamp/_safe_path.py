"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Portions of a Path take into account platform must be dealt withpSafely deal with paths.

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str, str]
   :value: ("fix_relpath", "is_linux", "is_macos", "is_win", \
   "replace_suffixes", "resolve_path", "resolve_joinpath", \
   "get_venv_python_abspath")

   Module exports

"""

import platform
import shutil
from pathlib import (
    Path,
    PurePath,
    PurePosixPath,
    PureWindowsPath,
)
from typing import cast

__all__ = (
    "fix_relpath",
    "is_linux",
    "is_macos",
    "is_win",
    "replace_suffixes",
    "resolve_path",
    "resolve_joinpath",
    "get_venv_python_abspath",
)


def is_linux():
    """Check platform is Linux.

    When messages are intended for Windows, but would like to see on
    Linux as well.

    :returns: True if platform is Linux
    :rtype: bool
    """
    ret = platform.system().lower() == "linux"

    return ret


def is_win():
    """Check platform is Windows

    :returns: True if platform is Windows
    :rtype: bool
    """
    ret = platform.system().lower() == "windows"

    return ret


def is_macos():
    """Check platform is MacOS

    :returns: True if platform is MacOS
    :rtype: bool
    """
    ret = platform.system().lower() == "darwin"

    return ret


def _to_purepath(relpath_b):
    """Convert a relative path to PurePath

    :param relpath_b: A posix style path. Requiring fixing before joinpath
    :type relpath_b: pathlib.PurePath | pathlib.Path | str
    :returns: Platform specific pure path
    :rtype: pathlib.PureWindowsPath | pathlib.PurePosixPath
    """
    if is_win():  # pragma: no cover no-cover-if-windows-no
        fix_b = PureWindowsPath(relpath_b)
    else:  # pragma: no cover no-cover-if-windows
        fix_b = PurePosixPath(relpath_b)

    return fix_b


def resolve_path(str_cmd):
    """Windows safe resolve executable path

    :param str_cmd: Relative path to executable
    :type str_cmd: str
    :returns: Windows safe absolute path to executable
    :rtype: str | None
    """
    str_path = shutil.which(str_cmd)
    if str_path is None:
        ret = None
    else:
        ret = str(_to_purepath(str_path))

    return ret


def fix_relpath(relpath_b):
    """Paths are normally expressed as posix paths. On Windows, relpath
    must be converted.

    ``src/complete_awesome_perfect/_version.py``

    becomes

    ``src\\complete_awesome_perfect\\_version.py``

    :param relpath_b: A posix style path. Requiring fixing before joinpath
    :type relpath_b: pathlib.PurePath | pathlib.Path | str
    :returns: Platform specific pure path
    :rtype: pathlib.PureWindowsPath | pathlib.PurePosixPath
    """
    fix_b = str(_to_purepath(relpath_b))

    return fix_b


def resolve_joinpath(abspath_a, relpath_b):
    """Windows safe joinpath. Fixes relative path

    :param abspath_a: A correct absolute path
    :type abspath_a: pathlib.PurePath | pathlib.Path
    :param relpath_b: A posix style path. Requiring fixing before joinpath
    :type relpath_b: pathlib.PurePath | pathlib.Path | str
    :returns: Platform specific pure path
    :rtype: pathlib.PureWindowsPath | pathlib.PurePosixPath | type[pathlib.Path]
    """
    str_fix_b = fix_relpath(relpath_b)
    is_path_subclass = issubclass(type(abspath_a), Path)
    if is_win():  # pragma: no cover no-cover-if-windows
        cls_pure = PureWindowsPath
    else:  # pragma: no cover no-cover-if-windows-no
        cls_pure = PurePosixPath

    if is_path_subclass:
        # WindowsPath or PosixPath
        ret = abspath_a.joinpath(str_fix_b)
    else:
        ret = cls_pure(abspath_a).joinpath(str_fix_b)

    return ret


def replace_suffixes(abspath_a, suffixes):
    """Replace suffixes.

    :param abspath_a:
    :type abspath_a: pathlib.PurePath | pathlib.Path
    :param suffixes:
    :type suffixes: str | None
    :returns: abspath with replaced suffixes
    :rtype: pathlib.PurePath | pathlib.Path
    """
    path_parent = abspath_a.parent
    str_name_0 = abspath_a.name

    # Get rid of all suffixes
    stem = str_name_0.split(".")[0]

    if suffixes is not None:
        str_name_1 = f"{stem}{suffixes}"
    else:
        str_name_1 = stem

    ret = path_parent / str_name_1

    return ret


def get_venv_python_abspath(path_cwd, venv_relpath):
    """Within the package base folder, venv(s) should have been created
    within subfolder(s).

    Given the package base folder and the venv relative path, get the
    platform specific python executable absolute path

    :param path_cwd: package base folder absolute path
    :type path_cwd: pathlib.Path | pathlib.PurePath
    :param venv_relpath:

       venv Base posix style relative path. Even for Windows.

    :type venv_relpath: str
    :returns: venv's python executable absolute path
    :rtype: str

    :raises:

       - :py:exc:`TypeError` -- 1st arg Unsupported type. Expecting Path or PurePath

       - :py:exc:`NotADirectoryError` -- Missing venv folder. May indicate run under
         gh workflow or tox

    """
    is_path_cwd_ng = path_cwd is None or not issubclass(type(path_cwd), PurePath)
    if is_path_cwd_ng:
        msg_warn = (
            "Expecting either Path or PurePath got unsupported type "
            f"{type(path_cwd)}"
        )
        raise TypeError(msg_warn)
    else:  # pragma: no cover
        pass

    """Guessing path to python executable.
    :code:`sys.executable` or :code:`sys._base_executable` are for the
    current venv. Which is unhelpful.
    """
    if is_win():  # pragma: no cover
        # Should be posix path. Even for Windows
        binary_posix_relpath = "Scripts/python.exe"
    else:  # pragma: no cover
        binary_posix_relpath = "bin/python"

    abspath_venv = cast("Path", resolve_joinpath(path_cwd, venv_relpath))
    is_venv_folder_exists = not abspath_venv.exists() and not abspath_venv.is_dir()

    if is_venv_folder_exists:
        """gh workflow and tox, only one Python executable.
        Would need to setup venv w/ appropriate and respective python interpretor
        """
        reason = "venv relative path did not find a folder containing a venv"
        raise NotADirectoryError(reason)
    else:
        abspath_venv_python = cast(
            "Path",
            resolve_joinpath(
                abspath_venv,
                binary_posix_relpath,
            ),
        )
        venv_python_abspath = str(abspath_venv_python)

    return venv_python_abspath
