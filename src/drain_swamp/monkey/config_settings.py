"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: __all__
   :type: tuple[str]
   :value: ("ConfigSettings",)

   Module exports

.. py:data:: log
   :type: logging.Logger

   Module level logger

"""

import logging
import os
import sys
from pathlib import (
    Path,
    PurePath,
)
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):  # pragma: no cover
    try:
        import tomllib
    except ImportError:
        # Help users on older alphas
        if not TYPE_CHECKING:
            import tomli as tomllib
else:  # pragma: no cover
    import tomli as tomllib

from ..constants import g_app_name
from .patch_pyproject_reading import ReadPyproject

__all__ = ("ConfigSettings",)
log = logging.getLogger(f"{g_app_name}.monkey.config_settings")


class ConfigSettings:
    """There is no clear guidance on how build module should communicate
    ``config settings`` command line options to the build back end.

    This is the communication flow:

    .. code-block:: text

       - build
         --> setuptools
             --> build front end
             --> build backend (within a subprocess)
                 --> (plugin) manager
                     --> build plugin

    Requires a PEP, for all to agree, on how to pass these config settings
    to the build backend subprocess

    In the meantime, **this is the work around** for communication with
    the build backend

    - create a environment variable, DS_CONFIG_SETTINGS, set value to path to a temp file

    - temp file is in ``pyproject.toml`` format/style. ``project.name`` and
      ``project.version`` are required but not used. Contains a section, "config-settings".
      That section, contains key/value pairs. Type are both str.

      Which key value pairs to pass in depends on what is required by
      build plugins. Current key pairs:

      ``kind = "tag"``

      ``set-lock = "1"``

    Paths must be single quoted, not double quoted. Otherwise On Windows,
    TOML file considered invalid

    :cvar SECTION_NAME: .toml file tool section name
    :vartype SECTION_NAME: str
    :cvar ENVIRON_KEY:

       Environment variable which stores the path to the temporary .toml
       file containing command line options intended for the build plugins

    :vartype ENVIRON_KEY: str
    :cvar FILE_NAME_DEFAULT: config settings temporary file name, not path
    :vartype FILE_NAME_DEFAULT: str
    :ivar file_name: Actual config settings temporary file name. Overrides default
    :vartype file_name: str | None
    """

    SECTION_NAME: str = "config-settings"
    ENVIRON_KEY: str = "DS_CONFIG_SETTINGS"
    FILE_NAME_DEFAULT: str = "setuptools-build.toml"

    __slots__ = ("_file_name",)

    def __init__(self, file_name=None):
        """Class constructor."""
        super().__init__()
        self.file_name = file_name

    @property
    def file_name(self):
        """Get config settings file name. This is a temporary file.

        :returns: config settings file name
        :rtype: str
        """
        return self._file_name

    @file_name.setter
    def file_name(self, val):
        """Override default config file file name.

        :param val: Expecting a str
        :type val: typing.Any
        """
        cls = type(self)
        is_none_or_empty = (
            val is None or not isinstance(val, str) or len(val.strip()) == 0
        )
        if is_none_or_empty:
            self._file_name = cls.FILE_NAME_DEFAULT
        else:
            self._file_name = val

    @classmethod
    def get_abs_path(cls):
        """From os.environ get temporary absolute file path.

        :returns:
        :rtype: str | None
        """
        ret = os.environ.get(cls.ENVIRON_KEY, None)
        return ret

    @classmethod
    def set_abs_path(cls, val):
        """Set absolute temporary file path to config settings .toml file.

        :param val: Expecting either str or Path. Should be absolute path
        :type val: typing.Any
        """
        if val is not None and issubclass(type(val), PurePath):
            toml_path = str(val)
        elif val is not None and isinstance(val, str):
            toml_path = val
        else:
            toml_path = None

        if toml_path is not None:
            os.environ[cls.ENVIRON_KEY] = toml_path
        else:  # pragma: no cover
            pass

    @classmethod
    def remove_abs_path(cls):
        """Remove environment variable holding the config settings temp file path."""
        del os.environ[cls.ENVIRON_KEY]

    def read(self):
        """Environment variable DS_CONFIG_SETTINGS contains an absolute
        path to a .toml file containing plugins' key/value pairs

        If :code:`python -m build` config setting cli options would be
        passed thru, by setuptools, this function would be unnecessary

        setuptools currently lacks this expected feature

        :returns:

           config settings dict. What normally would be supplied as
           :code:`python -m build` config setting cli options

        :rtype: dict[str, typing.Any]
        """
        cls = type(self)
        toml_path = cls.get_abs_path()
        if toml_path is not None:
            path_f = Path(toml_path)
            is_exists = path_f.exists() and path_f.is_file()
            if is_exists:
                """Attempt to read toml file. section tool.config-settings.
                Get all key/value pairs
                """
                try:
                    pyproj_data = ReadPyproject()(
                        path=path_f, tool_name=cls.SECTION_NAME
                    )
                except (LookupError, tomllib.TOMLDecodeError) as e:
                    d_section = {}
                    msg_warn = (
                        f"Either no section {cls.SECTION_NAME} or "
                        f"config_settings toml is invalid. {e}"
                    )
                    log.warning(msg_warn)
                else:
                    # from setuptools_scm._integration.toml import TOML_RESULT
                    d_section = pyproj_data.section

                    # No config settings. Log warning
                    if len(d_section.keys()) == 0:
                        msg_warn = (
                            "Expected env variable, DS_CONFIG_SETTINGS. Should contain "
                            "path to .toml file. File contains project.name, "
                            "project.version, tool.config-settings.kind and "
                            "tool.config-settings.set-lock"
                        )
                        log.warning(msg_warn)
                    else:  # pragma: no cover
                        pass

            else:  # pragma: no cover
                d_section = {}
        else:  # pragma: no cover
            d_section = {}

        return d_section

    def write(
        self,
        path_dir,
        toml_contents,
    ):
        """The temp file will contain key/value pairs used by the build plugins.
        setuptools does not currently pass config_settings, requires a PEP
        for all to agree on how to pass these config settings from
        build --> setuptools --> build front end --> build backend in a subprocess.

        In the meantime, **this is the work around** for communication with
        the build backend

        :param path_dir:

           Will create a throw away file, so folder usually in /tmp or equivalent

        :type path_dir: pathlib.Path
        :param toml_contents:

           In ``pyproject.toml`` style, so project.name and project.version are
           required, but not used. Has section, ``tool.config-settings``. With
           key/value pairs. Both key and value are str.

           Which key value pairs to pass in depends on what is required by
           build plugins. Current key pairs:

           - ``kind = "tag"``

           - ``set-lock = "1"``

        :type toml_contents: str
        :param file_name:

           Default "setuptools-build.toml". File name of the temp .toml file

        :type file_name: str | None
        """
        cls = type(self)
        # overwrite ok. Not previously exists ok
        path_toml = path_dir.joinpath(self.file_name)
        path_toml.write_text(toml_contents)

        # environment variable contains path to a .toml file in a tmp folder
        # The temp file will contain key/value pairs used by the build plugins
        cls.set_abs_path(path_toml)

    @classmethod
    def get_section_dict(cls, path_dir, toml_contents, file_name=None):
        """Set the config settings and returning the section mapping.

        :param path_dir:

           Will create a throw away file, so folder usually in /tmp or equivalent

        :type path_dir: pathlib.Path
        :param toml_contents:

           In ``pyproject.toml`` style, so project.name and project.version are
           required, but not used. Has section, ``tool.config-settings``. With
           key/value pairs. Both key and value are str.

           Which key value pairs to pass in depends on what is required by
           build plugins. Current key pairs:

           - ``kind = "tag"``

           - ``set-lock = "1"``

        :type toml_contents: str
        :param file_name:

           Default "setuptools-build.toml". File name of the temp .toml file

        :type file_name: str | None
        :returns:

           config settings dict. What normally would be supplied as
           :code:`python -m build` config setting cli options

        :rtype: dict[str, typing.Any]
        """
        cs = cls(file_name=file_name)
        cs.write(path_dir, toml_contents)
        d_section = cs.read()

        return d_section
