"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

``pyproject.toml`` parsing. text --> dict

.. py:data:: __all__
   :type: tuple[str]
   :value: ("TomlParser",)

   Module exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: is_module_debug
   :type: bool

   Module level debugging flag

"""

import logging
import sys
from pathlib import (
    Path,
    PurePath,
)
from typing import TYPE_CHECKING

from .constants import g_app_name
from .exceptions import (
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
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
__all__ = ("TomlParser",)

_logger = logging.getLogger(f"{g_app_name}.parser_in")
is_module_debug = False


class TomlParser:
    """Reverse searches for a ``pyproject.toml`` file and parses it.

    Interface provides both the dict and the resolved absolute path

    :ivar path:

       Starting search absolute path. Can be a folder or file. Reverse
       searches for a ``pyproject.toml`` file

    :vartype path: typing.Any | None
    :ivar raise_exceptions: Default False. Expecting a bool. If True raise exceptions
    :vartype raise_exceptions: typing.Any | None
    :raises:

       - :py:exc:`drain_swamp.exceptions.PyProjectTOMLReadError` --
         pyproject.toml either doesn't exist or inaccessible

       - :py:exc:`drain_swamp.exceptions.PyProjectTOMLParseError` --
         pyproject.toml unparsable

    """

    def __init__(self, path, raise_exceptions=False):
        """Class constructor."""
        super().__init__()
        if raise_exceptions is None or not isinstance(raise_exceptions, bool):
            raise_exceptions = False
        else:  # pragma: no cover
            pass

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
        """
        if path is None or not issubclass(type(path), PurePath):
            path_config = None
        else:
            path_config = path

        try:
            d_pyproject_toml = self._get_pyproject_toml(path_config)
        except PyProjectTOMLParseError:
            if raise_exceptions is True:
                raise
            else:
                d_pyproject_toml = None
        except (TypeError, FileNotFoundError) as e:
            if raise_exceptions is True:
                msg_warn = "pyproject.toml is either not a file or lacks r/w permission"
                raise PyProjectTOMLReadError(msg_warn) from e
            else:
                d_pyproject_toml = None

        self._d_pyproject_toml = d_pyproject_toml

    @property
    def path_file(self):
        """Absolute Path to ``pyproject.toml``.

        :returns:

           Absolute Path to ``pyproject.toml`` file. Not set if constructor
           raised an Exception

        :rtype: pathlib.Path | None
        """
        return self._path_file

    @property
    def d_pyproject_toml(self):
        """Getter pyproject.toml dict.

        :returns: pyproject.toml dict. Not set if constructor raised an Exception
        :rtype: collections.abc.Mapping[str, typing.Any] | None
        """
        return self._d_pyproject_toml

    @classmethod
    def resolve(cls, path_config):
        """Reverse search for a ``pyproject.toml`` file.

        Leverages reverse search algo from Python package, black

        :param path_config:

           Starting absolute path to reserve search for a ``pyproject.toml``.
           Expecting an absolute path either: Path or str

        :type path_config: typing.Any | None
        :returns: absolute path to a pyproject.toml
        :rtype: pathlib.Path
        :raises:

           - :py:exc:`TypeError` -- Start search path unsupported type
           - :py:exc:`FileNotFoundError` -- Reverse search pyproject.toml not found

        """
        meth_name = f"{g_app_name}.parser_in.{cls.__name__}.resolve_pyproject_toml"
        msg_exc_type_bad = f"Unsupported type expecting a Path. Got {path_config!r}"
        is_type_ng = path_config is None or not (
            isinstance(path_config, str) or issubclass(type(path_config), PurePath)
        )
        if is_type_ng:
            # unsupported type
            raise TypeError(msg_exc_type_bad)
        else:  # pragma: no cover
            pass

        if isinstance(path_config, str):
            path_file = Path(path_config)
        else:
            path_file = path_config

        msg_exc_no_such_file = (
            f"In {meth_name}, positional arg, no such file {path_file!s}"
        )

        # can be a file or dir or symlink. Try to resolve
        path_dir = path_file
        t_str = (str(path_dir),)

        if is_module_debug:  # pragma: no cover
            msg_info = f"{meth_name} t_str (before find_pyproject_toml): {t_str!r}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        file_path = find_pyproject_toml(t_str, None)
        if file_path is None:
            raise FileNotFoundError(msg_exc_no_such_file)
        else:
            path_file = Path(file_path)

        if is_module_debug:  # pragma: no cover
            msg_info = (
                f"{meth_name} path_file (after find_pyproject_toml): {path_file!r}"
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        return path_file

    def _get_pyproject_toml(self, path_config):
        """Load ``pyproject.toml``.

        Package click handles converting to :py:class:`pathlib.Path`.

        Example usage

        .. code-block:: text

           from drain_swamp.parser_in import get_pyproject_toml

           path_config = Path("[proj path]/requirements/prod.in")
           d_pyproject_toml = get_pyproject_toml(path_config)
           config_tables = d_pyproject_toml.get("tool", {}).get("setuptools", {}).get("dynamic", {})
           for (key, value) in config_tables.items():
               ...

        :param path_config: absolute path to ``pyproject.toml`` file or it's folder
        :type path_config: typing.Any | None
        :returns: tomllib dict. Cannot know yet which fields are needed
        :rtype: collections.abc.Mapping[str, typing.Any]
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
        cls = type(self)
        # may raise TypeError or FileNotFoundError
        self._path_file = cls.resolve(path_config)

        # tomllib insists on opened as binary
        with self._path_file.open(mode="rb") as f:
            try:
                d_ret = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                msg_exc_pyproject_toml = (
                    f"pyproject.toml either not found or cannot be parsed. "
                    f"path {self._path_file!s} exact issue: {e}"
                )
                raise PyProjectTOMLParseError(msg_exc_pyproject_toml)

        return d_ret

    @classmethod
    def read(
        cls,
        path_config,
    ):
        """Read the current contents of ``pyproject.toml`` file.

        :param path_config: ``pyproject.toml`` folder path
        :type path_config: pathlib.Path
        :returns: ``pyproject.toml`` dict and resolved path to file
        :rtype: tuple[dict[str, typing.Any], pathlib.Path]
        :raises:

           - :py:exc:`drain_swamp.exceptions.PyProjectTOMLParseError` --
             either not found or cannot be parsed

           - :py:exc:`drain_swamp.exceptions.PyProjectTOMLReadError` --
             Either not a file or lacks read permission

        """
        # Expects a Path. get_pyproject_toml call won't create a TypeError
        if is_module_debug:  # pragma: no cover
            msg_info = f"{cls.__name__}.read path_config: {path_config!r}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        is_type_ng = path_config is None or not (
            isinstance(path_config, str) or issubclass(type(path_config), PurePath)
        )

        # Avoids TypeError during resolve_pyproject_toml call
        if is_type_ng:
            msg_exc = "pyproject.toml is either not a file or lacks r/w permission"
            raise PyProjectTOMLReadError(msg_exc)
        else:  # pragma: no cover
            pass

        try:
            # raise TypeError, FileNotFoundError, or PyProjectTOMLParseError
            tp = cls(
                path_config,
                raise_exceptions=True,
            )
            d_pyproject_toml = tp.d_pyproject_toml
            path_f = tp.path_file
        except (PyProjectTOMLParseError, PyProjectTOMLReadError):
            raise

        return d_pyproject_toml, path_f
