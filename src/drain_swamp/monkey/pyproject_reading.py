"""
From setuptools-scm (MIT)

.. py:class:: TOML_RESULT

.. py:data:: TOML_RESULT
   :type: dict[str, typing.Any]
   :noindex:

   TOML dict

.. py:class:: TOML_LOADER

.. py:data:: TOML_LOADER
   :type: collections.abc.Callable[[str], TOML_RESULT]
   :noindex:

   A function that takes raw TOML str and converts into a TOML dict

.. py:data:: __all__
   :type: tuple[str, str, str, str]
   :value: ("TOML_LOADER", "TOML_RESULT", "read_toml_content", \
   "load_toml_or_inline_map")

   Module exports

.. seealso::

   `pyproject_reading.py <https://github.com/pypa/setuptools-scm/blob/main/src/setuptools_scm/_integration/toml.py>`_

"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import (
    Any,
    TypedDict,
    cast,
)

if sys.version_info >= (3, 11):  # pragma: no cover py-gte-311-else
    import tomllib
    from tomllib import loads as load_toml
else:  # pragma: no cover py-gte-311
    import tomli as tomllib
    from tomli import loads as load_toml

TOML_RESULT = dict[str, Any]
TOML_LOADER = Callable[[str], TOML_RESULT]

__all__ = (
    "TOML_LOADER",
    "TOML_RESULT",
    "read_toml_content",
    "load_toml_or_inline_map",
)


def read_toml_content(path, default=None):
    """Read a file if not found can return default. If found load file
    data as TOML

    :param path: absolute path to a TOML file
    :type path: pathlib.Path
    :param default: Default None. Allow some fallback if cannot load the TOML file.
    :type default: drain_swamp.monkey.pyproject_reading.TOML_RESULT | None
    :returns: TOML as a dict
    :rtype: drain_swamp.monkey.pyproject_reading.TOML_RESULT
    :raises:

       - :py:exc:`FileNotFoundError` -- TOML file not found. Check the absolute path

       - :py:exc:`tomllib.TOMLDecodeError` -- TOML parse error

    """
    try:
        data = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        if default is None:
            msg_exc = f"TOML file not found at {path!r}"
            raise FileNotFoundError(msg_exc) from exc
        else:  # pragma: no cover
            ret = default
    else:
        try:
            ret = load_toml(data)
        except tomllib.TOMLDecodeError:
            raise

    return ret


class _CheatTomlData(TypedDict):
    """Hack to pretend typing happened.

    .. py:attribute:: cheat
       :type: dict[str, typing.Any]

       The hack pretending type checked. By adding one level of nonsense.

    """

    cheat: dict[str, Any]


def load_toml_or_inline_map(data):
    """Load toml data - with a special hack if only an inline map is given

    This is a verified, in the unittest, inline map

    .. code-block:: text

       '{project = {name = "proj", version = "0.0.1"}}'

    :param data: Data read from a toml file
    :type data: typing.Any | None
    :returns: toml data as a dict
    :rtype: dict[str, typing.Any]
    """
    is_ng = data is None or not isinstance(data, str) or len(data.strip()) == 0
    if is_ng:
        ret = {}
    else:
        # non-empty str
        if data[0] == "{":
            # a dict with one column "cheat". Pretend it was TOML
            data = "cheat=" + data
            loaded: _CheatTomlData = cast(_CheatTomlData, load_toml(data))
            ret = loaded["cheat"]
        else:  # pragma: no cover
            # Actual TOML str
            ret = load_toml(data)

    return ret
