"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("is_ok", "is_relative_required", "is_iterable_not_str")

   Module exports

.. py:data:: DEFAULT_EXTENSIONS
   :type: tuple[str, ...]
   :value: (".in",)

   Acceptable file extensions.

"""

from __future__ import annotations

import sys
from pathlib import PurePath

from .constants import SUFFIX_IN

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import (
        Generator,
        Sequence,
    )
else:  # pragma: no cover
    from typing import (
        Generator,
        Sequence,
    )

__package__ = "drain_swamp"
__all__ = (
    "is_ok",
    "is_relative_required",
    "is_iterable_not_str",
)

DEFAULT_EXTENSIONS = (SUFFIX_IN,)
CLICK_TRUE = ("1", "true", "t", "yes", "y", "on")
CLICK_FALSE = ("0", "false", "f", "no", "n", "off")


def is_ok(test):
    """Check if non-empty str

    Edge case: contains only whitespace --> ``False``

    :param test: variable to test
    :type test: typing.Any | None
    :returns: ``True`` if non-empty str otherwise ``False``
    :rtype: bool

    """
    ret = False
    is_str = test is not None and isinstance(test, str)
    if is_str:
        # Edge case: contains only whitespace
        str_stripped = test.strip()
        ret = len(str_stripped) != 0
    else:
        ret = False

    return ret


def is_relative_required(
    path_relative=None,
    extensions=DEFAULT_EXTENSIONS,
) -> bool:
    """Check that is relative path with expected suffix

    :param path_relative: Default None. Intended to be a relative path
    :type path_relative: pathlib.Path | None
    :param extensions:

       Default :py:data:`~drain_swamp.check_type.DEFAULT_EXTENSIONS`.
       Acceptable file extensions.

    :type extensions: collections.abc.Sequence[str]
    :returns: If an acceptable relative path with appropriate suffix
    :rtype: bool
    :raises:

       - :py:exc:`ValueError` -- Expecting at least one suffix to use to compare
       - :py:exc:`TypeError` -- Unsupported type expected a sequence (tuple or list)

    """
    lst_ext = []
    if not is_iterable_not_str(extensions):
        msg_exc = "Unsupported type expected a sequence (tuple or list)"
        raise TypeError(msg_exc)
    else:  # pragma: no cover
        pass

    # If not a str, ignore it
    exts = [ext for ext in extensions if isinstance(ext, str)]

    # if needed, prepend a "."
    for ext in exts:
        if not ext.startswith("."):
            lst_ext.append(f".{ext}")
        else:
            lst_ext.append(ext)

    if len(lst_ext) == 0:
        msg_exc = (
            "Expecting at least one suffix to compare against the "
            "relative paths suffixes"
        )
        raise ValueError(msg_exc)
    else:  # pragma: no cover
        pass

    is_relative_path_acceptable = (
        path_relative is not None
        and issubclass(type(path_relative), PurePath)
        and not path_relative.is_absolute()
        and path_relative.suffixes == lst_ext
    )

    return is_relative_path_acceptable


def is_iterable_not_str(mixed):
    """Can be iterated thru, but not the false positive, str

    :param mixed: Something that hopefully can be iterated thru
    :type mixed: typing.Any | None
    :returns: True if suitable for iteration and not a scalar str otherwise False
    :rtype: bool
    """
    ret = (
        mixed is not None
        and (
            isinstance(mixed, Sequence)
            or isinstance(mixed, set)
            or isinstance(mixed, Generator)
        )
        and not isinstance(mixed, str)
    )

    return ret


def click_bool(val=None):
    """Simulate click.Bool

    :param val: str provided on the command line indicating boolean state
    :type val: str | None
    :returns:

       None if not provided. True if command line equivalent of True or
       False if the opposite equivalent

    :rtype: bool | None
    """
    if val is None:
        ret = None
    else:
        if val in CLICK_TRUE:
            ret = True
        elif val in CLICK_FALSE:
            ret = False
        else:
            ret = None

    return ret
