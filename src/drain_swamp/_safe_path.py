"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Portions of a Path take into account platform must be dealt withpSafely deal with paths.

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str]
   :value: ("fix_relpath", "is_linux", "is_macos", "is_win", \
   "replace_suffixes", "resolve_path", "resolve_joinpath")

   Module exports

"""

import platform
import shutil
from pathlib import (
    Path,
    PurePosixPath,
    PureWindowsPath,
)

__all__ = (
    "fix_relpath",
    "is_linux",
    "is_macos",
    "is_win",
    "replace_suffixes",
    "resolve_path",
    "resolve_joinpath",
)


def is_linux():  # pragma: no cover
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


def is_macos():  # pragma: no cover
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
    if is_win():  # pragma: no cover
        fix_b = PureWindowsPath(relpath_b)
    else:  # pragma: no cover
        fix_b = PurePosixPath(relpath_b)

    return fix_b


def resolve_path(str_cmd):
    """Windows safe resolve executable path

    :param str_cmd: Relative path to executable
    :type str_cmd: str
    :returns: Windows safe absolute path to executable
    :rtype: str
    """
    str_path = shutil.which(str_cmd)
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
    if is_win():  # pragma: no cover
        cls_pure = PureWindowsPath
    else:  # pragma: no cover
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
    :type suffixes: str
    :returns: abspath with replaced suffixes
    :rtype: pathlib.PurePath | pathlib.Path
    """
    path_parent = abspath_a.parent
    str_name_0 = abspath_a.name

    # Get rid of all suffixes
    stem = str_name_0.split(".")[0]

    str_name_1 = f"{stem}{suffixes}"
    ret = path_parent / str_name_1

    return ret
