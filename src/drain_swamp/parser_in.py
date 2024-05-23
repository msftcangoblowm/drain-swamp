"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

``pyproject.toml`` parsing. text --> dict

.. py:data:: __all__
   :type: tuple[str]
   :value: ("get_pyproject_toml",)

   Module exports

"""

from __future__ import annotations

import sys
from pathlib import (
    Path,
    PurePath,
)
from typing import TYPE_CHECKING

from .exceptions import PyProjectTOMLParseError
from .pep518_read import find_pyproject_toml

if sys.version_info >= (3, 11):  # pragma: no cover
    try:
        import tomllib
    except ImportError:
        # Help users on older alphas
        if not TYPE_CHECKING:
            import tomli as tomllib
else:  # pragma: no cover
    import tomli as tomllib

__package__ = "drain_swamp"
__all__ = ("get_pyproject_toml",)


def get_pyproject_toml(path_config):
    """Load pyproject.toml

    Package click handles converting to :py:class:`pathlib.Path`.

    Example usage

    .. code-block:: text

       from drain_swamp.parser_in import get_pyproject_toml

       path_config = Path("[proj path]/requirements/prod.in")
       d_pyproject_toml = get_pyproject_toml(path_config)
       config_tables = d_pyproject_toml.get("tool", {}).get("setuptools", {}).get("dynamic", {})
       for (key, value) in config_tables.items():
           ...

    :param path_config: absolute path to ``pyproject.toml`` file
    :type path_config: pathlib.Path
    :returns: tomllib dict. Cannot know yet which fields are needed
    :rtype: dict[str, typing.Any]
    :raises:

       - :py:exc:`drain_swamp.exceptions.PyProjectTOMLParseError` --
         parsing toml unsuccessful

       - :py:exc:`TypeError` -- positional arg unsupported type

       - :py:exc:`FileNotFoundError` -- positional arg does not exist or not a file

    .. todo:: demand for setup.cfg / setup.py ?

       There is no support for setup.cfg / setup.py

       Should there be?

    .. todo:: check r/w permissions

       Check file is read write. If not raise a PermissionError

    """
    meth_name = "get_pyproject_toml"
    msg_exc_type_bad = f"Unsupported type expecting a Path. Got {type(path_config)}"
    is_type_ok = path_config is None or not (
        issubclass(type(path_config), PurePath) or isinstance(path_config, str)
    )
    if is_type_ok:
        # unsupported type
        raise TypeError(msg_exc_type_bad)
    else:  # pragma: no cover
        pass

    if isinstance(path_config, str):
        path_file = Path(path_config)
    else:
        path_file = path_config

    msg_exc_no_such_file = (
        f"In {meth_name}, positional arg, no such file {str(path_file)}"
    )

    is_not_there = not path_file.is_absolute() or (
        path_file.is_absolute() and not path_file.exists()
    )
    if is_not_there:
        raise FileNotFoundError(msg_exc_no_such_file)
    else:  # pragma: no cover
        pass

    # Ensure we are dealing with ``pyproject.toml`` file
    if path_file.exists() and path_file.is_dir():
        path_dir = path_file
        t_str = (str(path_dir),)
        file_path = find_pyproject_toml(t_str, None)
        if file_path is None:
            raise FileNotFoundError(msg_exc_no_such_file)
        else:
            path_file = Path(file_path)
    elif path_file.exists() and path_file.is_file():
        # Check path_file.name?
        pass
    else:  # pragma: no cover
        # not a folder or file
        raise FileNotFoundError(msg_exc_no_such_file)

    # tomllib insists on opened as binary
    with path_file.open(mode="rb") as f:
        try:
            d_ret = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            msg_exc_pyproject_toml = (
                "pyproject.toml either not found or cannot be parsed"
            )
            raise PyProjectTOMLParseError(msg_exc_pyproject_toml) from e

    return d_ret


def get_d_pyproject_toml(path):
    """Get pyproject_toml dict

    See package_metadata.PackageMetadata for testing

    :param path:

       Default None. If the package has yet to be installed, fallback
       to ``pyproject.toml``

    :type path: typing.Any | None
    :returns: pyproject.toml as a dict otherwise None
    :rtype: dict[str, typing.Any] | None
    """
    is_dir = (
        path is not None
        and issubclass(type(path), PurePath)
        and path.exists()
        and path.is_dir()
        and path.joinpath("pyproject.toml").exists()
        and path.joinpath("pyproject.toml").is_file()
    )
    is_pyproject_toml = (
        path is not None
        and issubclass(type(path), PurePath)
        and path.exists()
        and path.is_file()
        and path.name == "pyproject.toml"
    )

    if is_dir:
        path_config = path.joinpath("pyproject.toml")
    elif is_pyproject_toml:
        path_config = path
    else:
        path_config = None

    try:
        d_pyproject_toml = get_pyproject_toml(path_config)
    except (PyProjectTOMLParseError, TypeError):
        d_pyproject_toml = None

    return d_pyproject_toml
