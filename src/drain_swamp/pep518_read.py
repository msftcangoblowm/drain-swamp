"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

These :pep:`518` (aka pyproject.toml) functions are **not** app specific

These functions are lifted from the black project. With minor changes:

- Removed black specific version handling
- Added sphinx style code documentation
- Removed py38 styles typing like: Tuple or Dict
- Import Sequence correctly

.. seealso::

   ``pyproject.toml`` handling

   - :py:mod:`black`

.. note:: Flake8 config files handling

   Flake8
   `load_config <https://github.com/PyCQA/flake8/blob/fb9a02aaf77b56fcad4320971e7edca0cea93489/src/flake8/options/config.py#L56>`_
   function

   Monkeypatch of configparser to support pyproject.toml,
   `ConfigParserTomlMixin <https://github.com/csachs/pyproject-flake8/blob/16b9dd4d2f19dcf0bfb3a3110f98227627cd67fe/pflake8/__init__.py#L22>`_

   Apply monkeypatch
   `FixFilenames.apply <https://github.com/csachs/pyproject-flake8/blob/16b9dd4d2f19dcf0bfb3a3110f98227627cd67fe/pflake8/__init__.py#L86>`_

**Module private variables**

.. py:attribute:: __all__
   :type: tuple[str]
   :value: ("find_project_root", "find_pyproject_toml")

   Exported objects from this module

**Module objects**

"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import Sequence  # noqa: F401 Used by sphinx
else:  # pragma: no cover
    from typing import Sequence  # noqa: F401 Used by sphinx

__package__ = "drain_swamp"
__all__ = (
    "find_project_root",
    "find_pyproject_toml",
)


def _is_ok(test):
    """Check if non-empty str.

    Edge case: contains only whitespace --> ``False``

    :param test: variable to test
    :type test: typing.Any | None
    :returns: ``True`` if non-empty str otherwise ``False``
    :rtype: bool

    .. note::

       Vendored logging-strict.util.check_type.is_ok, so current module
       can be stand alone

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


def find_project_root(srcs, stdin_filename=None):
    """Return folder containing .git, .hg, or ``pyproject.toml``.

    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.

    Returns a two-tuple with the first element as the project root path and
    the second element as a string describing the method by which the
    project root was discovered.

    :param srcs:

       Files or folders, for files will take the parent folder.
       Potential folders that may contain ``pyproject.toml``

    :type srcs: collections.abc.Sequence[typing.Any] | None

    :param stdin_filename:

       Default ``None``. stdin file name, considers files parent as the
       project top folder

    :type stdin_filename: str | None
    :returns:

       Folder containing .git, .hg, or ``pyproject.toml``, will be a common
       parent of all files and directories passed in
       :paramref:`~drain_swamp.pep518_read.find_project_root.params.srcs`

    :rtype: tuple[pathlib.Path, str]
    :raises:

       - :py:exc:`PermissionError` -- Unreadable folder. Ungracefully handled

    .. note::

       Passing ``pyproject.toml``, by stdin, could be useful for testing recipes

    .. warning::

       functools.lru_cache causes optional parameter stdin_filename to **NOT BE OPTIONAL**

    .. seealso::

       :py:func:`black.files.find_project_root` source and credit Black

    """

    def is_sequence_empty(some_sequence: Sequence[Any] | None) -> bool:
        """Empty sequence check.

        :param some_sequence: Check if not None and an empty sequence
        :type some_sequence: collections.abc.Sequence[typing.Any] | None
        :returns: True if a Sequence.
        :rtype: bool
        """
        ret = (
            some_sequence is not None
            and isinstance(some_sequence, Sequence)
            and len(some_sequence) == 0
        )
        return ret

    def is_none(arg: Any) -> bool:
        """None check.

        :param arg: A value to check. True if is None.
        :type arg: typing.Any
        """
        ret = arg is None
        return ret

    def is_sequence_none(some_sequence: Sequence[Any] | None) -> bool:
        """Non-empty sequence of len 1.

        :param some_sequence: Check if not None and a sequence with one item.
        :type some_sequence: collections.abc.Sequence[typing.Any] | None
        :returns: True if a Sequence with one item.
        :rtype: bool
        """
        ret = (
            some_sequence is not None
            and isinstance(some_sequence, Sequence)
            and len(some_sequence) == 1
            and some_sequence[0] is None
        )
        return ret

    is_use_cwd = is_none(srcs) or is_sequence_none(srcs)
    if is_use_cwd:
        # Intention is: use cwd
        # None or Sequence[None]
        cwd_path = str(Path.cwd().resolve())
        srcs = []
        srcs.append(cwd_path)
    else:
        """Signature is intended to be Sequence[str], but assume
        Sequence[Any]. Filter out non-str, including None and str
        containing only whitespace"""
        srcs = [src for src in srcs if _is_ok(src)]

        if stdin_filename is not None and len(srcs) != 0:
            srcs = list(stdin_filename if s == "-" else s for s in srcs)
        elif stdin_filename is None and len(srcs) != 0:  # pragma: no cover
            # Added "-", but didn't supply :paramref:`stdin_filename`
            srcs = [s for s in srcs if s != "-"]
        else:  # pragma: no cover
            pass

    if is_none(srcs) or is_sequence_empty(srcs):  # pragma: no cover fallback
        srcs = [str(Path.cwd().resolve())]
    else:  # pragma: no cover
        pass

    path_srcs = [Path(Path.cwd(), src).resolve() for src in srcs]

    # A list of lists of parents for each 'src'. 'src' is included as a
    # "parent" of itself if it is a directory
    src_parents = [
        list(path.parents) + ([path] if path.is_dir() else []) for path in path_srcs
    ]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )

    for directory in (common_base, *common_base.parents):
        if (directory / ".git").exists():
            return directory, ".git directory"
        else:  # pragma: no cover
            pass

        if (directory / ".hg").is_dir():
            return directory, ".hg directory"
        else:  # pragma: no cover
            pass

        if (directory / "pyproject.toml").is_file():
            return directory, "pyproject.toml"
        else:  # pragma: no cover
            pass

    return directory, "file system root"


def find_pyproject_toml(path_search_start, stdin_filename):
    """Find the absolute filepath to a ``pyproject.toml`` if it exists.

    :param path_search_start:

       absolute paths of files or folders to start search for project base folder

    :type path_search_start: tuple[str, ...]
    :param stdin_filename: ``pyproject.toml`` passed into stdin. May be a file
    :type stdin_filename: str | ``None``
    :returns: Absolute path to project ``pyproject.toml`` otherwise ``None``
    :rtype: str | ``None``
    """
    """2nd item, reason, is string describing the method by which the project
    root was discovered"""
    try:
        path_project_root, _ = find_project_root(path_search_start, stdin_filename)
    except PermissionError:  # pragma: no cover
        # Causing PermissionError is platform.system dependent
        return None
    else:
        path_pyproject_toml = path_project_root / "pyproject.toml"
        if path_pyproject_toml.is_file():
            return str(path_pyproject_toml)
        else:
            return None
