"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Utils for handling: .in, .shared.in, .unlock, .shared.unlock, .lock, and .shared.lock

.. py:data:: ENDING
   :type: tuple[str, str, str]
   :value: (".in", ".unlock", ".lock")

   End suffix indicating one of the requirement lock file types

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str]
   :value: ("ENDINGS", "is_shared", "replace_suffixes_last", \
   "is_suffixes_ok", "check_relpath", "abspath_relative_to_package_base_folder")

   Module exports

"""

import logging
from pathlib import (
    Path,
    PurePath,
)
from typing import (
    Any,
    cast,
)

from ._safe_path import (
    replace_suffixes,
    resolve_joinpath,
)
from .check_type import is_ok
from .constants import g_app_name

ENDINGS = (".in", ".unlock", ".lock")
__all__ = (
    "ENDINGS",
    "abspath_relative_to_package_base_folder",
    "is_shared",
    "replace_suffixes_last",
    "is_suffixes_ok",
    "check_relpath",
)
is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.lock_util")


def is_shared(file_name: str) -> bool:
    """Determine if file name indicates requirements shared by more than one venv

    :param file_name: File name w/ or w/o (.in, .lock, or .unlock) ending
    :type file_name: str
    :returns: True if file suffix indicates shared by more than one venv otherwise False
    :rtype: bool
    :raises:

        - :py:exc:`ValueError` -- None, not str, or just whitespace or empty string

    """
    is_ng = (
        file_name is None
        or not isinstance(file_name, str)
        or len(file_name.strip()) == 0
    )
    if is_ng:
        msg_warn = (
            "file name cannot be None or unsupported type or contain "
            f"only whitespace. Got {type(file_name)}"
        )
        raise ValueError(msg_warn)
    else:  # pragma: no cover
        pass

    is_no_suffixes = len(Path(file_name).suffixes) == 0
    if is_no_suffixes:
        # Possibly a [[tool.venvs]].reqs relpath which lacks an ENDING
        ret = False
    else:
        # Has at least one suffix
        has_ending = any([file_name.endswith(ending) for ending in ENDINGS])
        # Strip ending if has one
        file_stem = Path(file_name).stem if has_ending else file_name
        # Test suffix, if has one, is ``.shared``
        ret = Path(file_stem).suffix == ".shared"

    return ret


def replace_suffixes_last(
    abspath_f: Any,
    suffix_last: str,
) -> Path:
    """Replace the last suffix of an absolute Path. Preserves ``.shared`` suffix

    :param abspath_f: Absolute path. Should be a Path, not PurePath
    :type abspath_f: typing.Any
    :param suffix_last: Suffix to replace existing last suffix. Preserves ``.shared``
    :type suffix_last: str
    :returns: Absolute path with last suffix replaced
    :rtype: pathlib.Path
    :raises:

        - :py:exc:`TypeError` -- PurePath unsupported type
        - :py:exc:`TypeError` -- Not a Path unsupported type
        - :py:exc:`ValueError` -- Not an absolute Path

    """
    is_purepath = (
        abspath_f is not None
        and not isinstance(abspath_f, Path)
        and issubclass(type(abspath_f), PurePath)
    )
    is_not_path = abspath_f is not None and not isinstance(abspath_f, Path)
    if is_purepath:
        msg_exc = (
            f"Unsupported type ({type(abspath_f)}). A PurePath cannot "
            "perform path operations. Provide a Path."
        )
        raise TypeError(msg_exc)
    elif is_not_path:
        msg_exc = f"Unsupported type ({type(abspath_f)}). Expecting an absolute Path"
        raise TypeError(msg_exc)
    elif (
        abspath_f is not None
        and isinstance(abspath_f, Path)
        and not abspath_f.is_absolute()
    ):
        msg_exc = "Expecting an absolute Path"
        raise ValueError(msg_exc)
    else:  # pragma: no cover
        pass

    # Contains a ``.shared`` suffix
    is_shared_suffix = is_shared(abspath_f.name)
    if is_shared_suffix:
        str_shared = ".shared"
    else:
        str_shared = ""

    path_out = cast(
        "Path",
        replace_suffixes(abspath_f, f"{str_shared}{suffix_last}"),
    )

    return path_out


def is_suffixes_ok(path_either: Any) -> Path:
    """Check has a suffix and last suffix either .in, .lock, .unlock

    :param path_either: Path either relative or absolute
    :type path_either: pathlib.Path
    :returns: True if suffixes ok otherwise False
    :rtype: bool
    :raises:

       - :py:exc:`ValueError` -- No suffixes. Expected suffixes
         e.g. .shared.in, .in, .lock, .unlock

       - :py:exc:`ValueError` -- Suffix is .shared, but lacks last suffix

       - :py:exc:`ValueError` -- Unexpected last suffix

       - :py:exc:`TypeError` -- Unsupported type. Expecting Path or pathlike str

    """
    is_path = path_either is not None and issubclass(type(path_either), PurePath)
    if is_ok(path_either):
        path_f = Path(path_either)
    elif is_path:
        path_f = path_either
    else:  # pragma: no cover
        msg_warn = (
            f"Unsupported type. Expecting Path got or pathlike str {type(path_either)}"
        )
        raise TypeError(msg_warn)

    # May be absolute or relpath
    relpath_suffix_last = path_f.suffix
    relpath_name = path_f.name
    relpath_suffixes = path_f.suffixes
    suffixes_count = len(relpath_suffixes)
    is_no_suffixes = suffixes_count == 0
    if is_no_suffixes:
        # no suffixes
        msg_warn = (
            f"Path {path_f!r} expected to have one or more suffix "
            "e.g. .shared.in, .in, .unlock, .lock, ..."
        )
        ret = False
    else:
        if suffixes_count == 1 and is_shared(relpath_name):
            # shared, but lacks .in, .unlock, or .lock
            msg_warn = (
                f"Path {path_f!r} suffix is .shared, but lacks last "
                f"suffix. Either: {ENDINGS}"
            )
            ret = False
        elif relpath_suffix_last not in ENDINGS:
            # not an expected last suffix
            msg_warn = (
                f"Path {path_f!r} suffix can optionally "
                f"include .shared, and should have either of these: {ENDINGS}"
            )
            ret = False
        else:
            # Acceptable relpath
            ret = True

    if not ret:
        raise ValueError(msg_warn)
    else:  # pragma: no cover
        pass

    return path_f


def check_relpath(cwd, path_to_check):
    """Check file exists and is relative to cwd. Should not be a str

    :param cwd: Package base folder
    :type cwd: pathlib.Path
    :param path_to_check: Hopefully a relative Path
    :type path_to_check: typing.Any
    :raises:

       - :py:exc:`TypeError` -- Sequence contains one or more unsupported types
       - :py:exc:`ValueError` -- Requirements file, (.in), not relative to base folder
       - :py:exc:`FileNotFoundError` -- Requirements file, (.in), not found

    """
    # contains only Path
    is_path = path_to_check is not None and issubclass(type(path_to_check), PurePath)
    if not is_path:
        msg_exc = f"in_files Sequence contains unsupported type, {type(path_to_check)}"
        raise TypeError(msg_exc)
    else:  # pragma: no cover
        pass

    # FileNotFoundError
    if path_to_check.is_absolute():
        abspath_to_check = path_to_check
        is_abs_path = path_to_check.is_file()
    else:
        abspath_to_check = resolve_joinpath(cwd, path_to_check)
        is_abs_path = abspath_to_check.is_file()

    if not is_abs_path:
        msg_exc = "Requirement (.in) file does not exist"
        raise FileNotFoundError(msg_exc)
    else:  # pragma: no cover
        pass

    # relative to self.cwd
    try:
        abspath_to_check.relative_to(cwd)
    except Exception as e:
        msg_exc = (
            f"requirements file, {abspath_to_check!r}, not relative to folder, {cwd!r}"
        )
        raise ValueError(msg_exc) from e


def abspath_relative_to_package_base_folder(
    abspath_cwd,
    abspath_f,
    constraint_relpath,
):
    """constraint|requirement relpath is relative to requirements file,
    not the package base folder (cwd). Get absolute path relative to
    cwd

    path components

    .. code-block:: text

        abspath_cwd + relative_relpath_dir + constraint_relpath

    relative_relpath_dir is the folders difference between abspath_f and cwd

    **Different folder example**

    - docs/pip-tools.in
    - requirements/pins.shared.in (constraint)

    ``docs/pip-tools.in`` contains line ``-c ../requirements/pins.shared.in``

    **relative_relpath_dir**
    From cwd perspective, ``docs/pip-tools.in`` is in ``docs``

    Final path components ``[abspath]`` + ``docs`` + ``../requirements/pins.shared.in``
    Resolves to ``[abspath/]requirements/pins.shared.in``

    **Same folder example**

    - requirements/pip-tools.in
    - requirements/pip.in (constraint)

    ``requirements/pip-tools.in`` contains line ``-c pin.in``

    **relative_relpath_dir**
    From cwd perspective, ``requirements/pip-tools.in`` is in ``requirements``

    Final path components ``[abspath]`` + ``requirements`` + ``pip.in``
    Resolves to ``[abspath/]requirements/pip.in``

    :param abspath_cwd: Absolute path of the cwd
    :type abspath_cwd: pathlib.Path
    :param abspath_f: Absolute path to the FilePin file
    :type abspath_f: pathlib.Path
    :param constraint_relpath:

       constraint|requirement relpath is relative to FilePin, not cwd

    :type constraint_relpath: str
    :returns: Resolved absolute Path to the constraint file
    :rtype: pathlib.Path
    :raises:

        - :py:exc:`FileNotFoundError` -- Path resolve did not find the file

    """
    dotted_path = f"{g_app_name}.lock_util.abspath_relative_to_package_base_folder"
    abspath_relative_to = abspath_f.parent
    relative_relpath_dir = abspath_relative_to.relative_to(abspath_cwd)

    # To visualize different between the FilePins and constraints paths
    relative_parent_count = len(relative_relpath_dir.parents)

    if is_module_debug:  # pragma: no cover
        msg_info = (
            f"{dotted_path} cwd {abspath_cwd} "
            f"constraint_relpath {constraint_relpath} "
            f"relative to {relative_relpath_dir} "
            f"relative_parent_count {relative_parent_count}"
        )
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    # abspath_cwd + relative_relpath_dir + constraint_relpath
    # If relative_parent_count == 0 then relative_relpath_dir = Path(".")
    abspath_constraint = cast(
        "Path",
        resolve_joinpath(abspath_cwd, relative_relpath_dir),
    )
    abspath_constraint = cast(
        "Path",
        resolve_joinpath(abspath_constraint, constraint_relpath),
    )

    if is_module_debug:  # pragma: no cover
        msg_info = (
            f"{dotted_path} abspath_constraint (before resolve) "
            f"{abspath_constraint}"
        )
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    try:
        abspath_constraint = abspath_constraint.resolve(strict=True)
    except OSError as exc:
        msg_warn = str(exc)
        raise FileNotFoundError(msg_warn) from exc

    if is_module_debug:  # pragma: no cover
        msg_info = (
            f"{dotted_path} abspath_constraint (after resolve) {abspath_constraint}"
        )
        _logger.info(msg_info)
    else:  # pragma: no cover
        pass

    return abspath_constraint
