"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Utils for handling: .in, .shared.in, .unlock, .shared.unlock, .lock, and .shared.lock

.. py:data:: ENDING
   :type: tuple[str, str, str]
   :value: (".in", ".unlock", ".lock")

   End suffix indicating one of the requirement lock file types

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("is_shared", "replace_suffixes_last")

   Module exports

"""

from pathlib import (
    Path,
    PurePath,
)
from typing import (
    Any,
    cast,
)

from ._safe_path import replace_suffixes

ENDINGS = (".in", ".unlock", ".lock")
__all__ = (
    "is_shared",
    "replace_suffixes_last",
)


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
