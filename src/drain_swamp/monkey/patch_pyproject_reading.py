"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

setuptools_scm._integration.pyproject_reading.read_pyproject is too
strict, monkeypatch it!

Without the patch, pyproject.toml [tool.setuptools-scm] section is
missing, raises :py:exc:`LookupError`.

.. warning:: tool_name ordering

   tool_name requires 1st [tool.x] section to be the package name, in
   this case, drain-swamp. e.g. [tool.drain-swamp] section

**CHANGES**

- tool_name (str -> str | Sequence[str])
  from "setuptools-scm"
  to ["drain-swamp", "pipenv-unlock"]

- the tool_name becomes the first element

- combines contents of sections

**USAGE**

.. code-block:: text

   from unittest.mock import patch
   from drain_swamp.monkey.setuptools_scm_pyproject_reading import read_pyproject
   with patch("setuptools_scm._config._read_pyproject", wraps=read_pyproject):
       ...

.. seealso::

   https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_integration/pyproject_reading.py
   https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_config.py

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("ReadPyproject", "ReadPyprojectStrict")

   Module exports

.. py:data:: log
   :type: logging.Logger

   module level logger

"""

import abc
from pathlib import Path
from typing import NamedTuple

import setuptools_scm._log
from setuptools_scm._integration.toml import (
    TOML_RESULT,
    read_toml_content,
)

log = setuptools_scm._log.log.getChild("pyproject_reading")

__all__ = (
    "ReadPyproject",
    "ReadPyprojectStrict",
)


class PyProjectData(NamedTuple):
    """Data class for holding contents of a section.

    :cvar path: config file Path
    :vartype path: pathlib.Path
    :cvar tool_name: section name
    :vartype tool_name: str
    :cvar project: Project section contents
    :vartype project: setuptools_scm._integration.toml.TOML_RESULT
    :cvar section: Section contents
    :vartype section: setuptools_scm._integration.toml.TOML_RESULT
    """

    path: Path
    tool_name: str
    project: TOML_RESULT
    section: TOML_RESULT

    @property
    def project_name(self):
        """Getter for project.name

        :returns: package name
        :rtype: str | None
        """
        return self.project.get("name")


class ReadPyprojectBase(abc.ABC):
    """From a pyproject.toml file, ABC for key/value pairs from a section."""

    @abc.abstractmethod
    def update(self, d_target, d_other):
        """Subclass overload so can filter d_other.

        :param d_target: parent dict
        :type d_target: dict[str, typing.Any]
        :param d_other: dict. Update parent
        :type d_other: dict[str, typing.Any]
        """
        ...

    def __call__(
        self,
        path=Path("pyproject.toml"),
        tool_name=["drain-swamp", "pipenv-unlock"],
        require_section=True,
    ):
        """Read in pyproject.toml and if necessary combine multiple sections into one.

        Previously raised :py:exc:`FileNotFoundError` and :py:exc:`LookupError`
        instead will produce an empty dict

        :param path: Defaults to :code:`Path("pyproject.toml")` Absolute path to toml file
        :type path: pathlib.Path
        :param tool_name:

           Default ["drain-swamp", "pipenv-unlock"]. ``pyproject.toml``
           sections name or section name. First section name **MUST** be the package name

        :type tool_name: str | Sequence[str]
        :param require_section:

           Default True. This is ignored. Prevents extending package
           features and the possibility of pulling in multiple sections

        :type require_section: bool
        :returns: A convenience representation of ``pyproject.toml`` file
        :rtype: PyProjectData
        :raises:

           - :py:exc:`LookupError` -- Either toml file parsing failed
             or no such section

        """
        if isinstance(tool_name, str):
            seq_tool = (tool_name,)
        else:
            # assumes a Sequence[str]
            seq_tool = tool_name

        try:
            defn = read_toml_content(path)
        except FileNotFoundError:
            # None if require_section else {}
            defn = {}

        # Combine sections
        # Was preventing extending setuptools_scm
        d_section: TOML_RESULT = {}
        for tool_name in seq_tool:
            try:
                section = defn.get("tool", {})[tool_name]
            except (KeyError, LookupError) as e:
                error = f"{path} does not contain a tool.{tool_name} section"
                msg_warn = f"toml section missing {error!r}"
                # log.warning(msg_warn, exc_info=True)
                raise LookupError(msg_warn) from e
            else:
                # subclass must implement method, ``update``
                self.update(d_section, section)

        project = defn.get("project", {})

        # Use 1st tool name
        tool_name_2: str = seq_tool[0]

        return PyProjectData(path, tool_name_2, project, d_section)


class ReadPyproject(ReadPyprojectBase):
    """Do not confine data fields. Accept whatever the section(s) contains."""

    def update(self, d_target, d_other):
        """
        :param d_target: parent dict
        :type d_target: dict[str, typing.Any]
        :param d_other: dict. Update parent
        :type d_other: dict[str, typing.Any]
        """
        d_target.update(d_other)


class ReadPyprojectStrict(ReadPyprojectBase):
    """Confine data fields to acceptable by setuptools_scm._config.Configuration."""

    def update(self, d_target, d_other):
        """Confine to only setuptools_scm._config.Configuration data fields.

        :param d_target: parent dict
        :type d_target: dict[str, typing.Any]
        :param d_other: dict. Update parent
        :type d_other: dict[str, typing.Any]
        """
        # import dataclasses
        # from setuptools_scm._config import Configuation
        # [field.name for field in fields(Configuration)]
        keys_allowed = (
            "relative_to",
            "root",
            "version_scheme",
            "local_scheme",
            "tag_regex",
            "parentdir_prefix_version",
            "fallback_version",
            "fallback_root",
            "write_to",
            "write_to_template",
            "version_file",
            "version_file_template",
            "parse",
            "git_describe_command",
            "dist_name",
            "version_cls",
            "search_parent_directories",
            "parent",
        )
        # dict comprehension to filter dict keys
        d_y = {k: v for k, v in d_other.items() if k in keys_allowed}
        d_target.update(d_y)
