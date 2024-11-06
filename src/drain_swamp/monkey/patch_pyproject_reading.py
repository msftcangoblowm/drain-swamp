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

.. seealso::

   setuptools-scm
   `config <https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_config.py>`_

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("ReadPyproject", "ReadPyprojectStrict")

   Module exports

.. py:data:: log
   :type: logging.Logger

   module level logger

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Turn on during debugging

"""

from __future__ import annotations

import abc
import logging
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import NamedTuple

from ..constants import g_app_name
from .pyproject_reading import (
    TOML_RESULT,
    read_toml_content,
)

log = logging.getLogger(f"{g_app_name}.monkey.patch_pyproject_reading")
is_module_debug = False

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
    :vartype section: setuptools_scm._integration.toml.TOML_RESULT | collections.abc.Sequence[setuptools_scm._integration.toml.TOML_RESULT]
    """

    path: Path
    tool_name: str
    project: TOML_RESULT
    section: TOML_RESULT | Sequence[TOML_RESULT]

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
    def update(
        self,
        d_target,
        d_other,
        key_name: str | None = None,
        key_value: str | None = None,
    ):
        """Subclass overload so can filter d_other.

        :param d_target: parent dict
        :type d_target: TOML_RESULT | collections.abc.Sequence[TOML_RESULT]
        :param d_other: dict. Update parent
        :type d_other: TOML_RESULT
        :param key_name:

           None if not a ``collections.abc.Sequence[dict]``. To identify
           which dict to update, a known dict key is searched for.

        :type key_name: str | None
        :param key_value:

           None if not a ``collections.abc.Sequence[dict]``. To identify
           which dict to update, a known dict key / value pair are used
           to find a match.

        :type key_value: str | None
        """
        ...

    def __call__(
        self,
        path=Path("pyproject.toml"),
        tool_name=["drain-swamp", "pipenv-unlock"],
        require_section=True,
        key_name: str | None = None,
        is_expect_list: bool = False,
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
        :param key_name:

           None if not a ``collections.abc.Sequence[dict]``. To identify
           which dict to update, a known dict key is searched for.

        :type key_name: str | None
        :param is_expect_list:

           Default False. Do not accept a TOML table (dict) when want
           a TOML array of tables list[dict]

        :type is_expect_list: bool
        :returns: A convenience representation of ``pyproject.toml`` file
        :rtype: PyProjectData
        :raises:

           - :py:exc:`FileNotFoundError` -- pyproject.toml not found

           - :py:exc:`LookupError` -- Either toml file parsing failed
             or no such section

           - :py:exc:`KeyError` -- pyproject.toml section not found

        .. todo::

           Do a reverse search for the pyproject.toml file

        """
        mod_path = (
            "drain_swamp.monkey.patch_pyproject_reading.ReadPyprojectBase.__call__"
        )
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

        if is_module_debug:  # pragma: no cover
            msg_info = f"In {mod_path}, toml contents {defn}"
            log.info(msg_info)
        else:  # pragma: no cover
            pass

        # Combine sections
        # Was preventing extending setuptools_scm
        d_section: TOML_RESULT = {}
        lst_section: Sequence[TOML_RESULT] = []
        is_section_dict = False
        is_section_list = False
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

                if is_module_debug:  # pragma: no cover
                    msg_info = f"In {mod_path}, section {type(section)}"
                    log.info(msg_info)
                else:  # pragma: no cover
                    pass

                is_key_name_ok = (
                    key_name is not None
                    and isinstance(key_name, str)
                    and len(key_name.strip()) != 0
                )

                if isinstance(section, Mapping) and not is_expect_list:
                    self.update(d_section, section)
                    is_section_dict = True
                elif isinstance(section, Sequence) and is_key_name_ok:
                    is_section_list = True
                    for d_item in section:
                        if is_module_debug:  # pragma: no cover
                            msg_info = f"In {mod_path}, call update(before) {d_item}"
                            log.info(msg_info)
                        else:  # pragma: no cover
                            pass

                        self.update(
                            lst_section,
                            d_item,
                            key_name=key_name,
                            key_value=d_item[key_name],
                        )

                        if is_module_debug:  # pragma: no cover
                            msg_info = (
                                f"In {mod_path}, call update(after) {lst_section}"
                            )
                            log.info(msg_info)
                        else:  # pragma: no cover
                            pass

                    if is_module_debug:  # pragma: no cover
                        msg_info = f"In {mod_path}, finally {lst_section}"
                        log.info(msg_info)
                    else:  # pragma: no cover
                        pass
                else:  # pragma: no cover
                    pass

        if not is_section_dict and not is_section_list:
            msg_warn = (
                f"In {path!s} tool.{tool_name} section expected either "
                f"a list or a dict. Got {section!r}"
            )
            raise LookupError(msg_warn)
        else:  # pragma: no cover
            pass

        project = defn.get("project", {})

        # Use 1st tool name
        tool_name_2: str = seq_tool[0]

        if is_section_dict:
            section_mixed = d_section
        else:
            section_mixed = lst_section

        ret = PyProjectData(path, tool_name_2, project, section_mixed)

        return ret


class ReadPyproject(ReadPyprojectBase):
    """Do not confine data fields. Accept whatever the section(s) contains."""

    def update(
        self,
        mixed_target,
        d_other,
        key_name: str | None = None,
        key_value: str | None = None,
    ):
        """Update a ReadPyprojectBase subclass instance. Which is either
        a dict or a list[dict].

        For list[dict] also supply a key / value pair. So know which dict to update.

        :param mixed_target: parent dict
        :type mixed_target: dict[str, typing.Any] | collections.abc.Sequence[dict[str, typing.Any]]
        :param d_other: dict. Update parent
        :type d_other: dict[str, typing.Any]
        :param key_name:

           None if not a ``collections.abc.Sequence[dict]``. To identify
           which dict to update, a known dict key is searched for.

        :type key_name: str | None
        :param key_value:

           None if not a ``collections.abc.Sequence[dict]``. To identify
           which dict to update, a known dict key / value pair are used
           to find a match.

        :type key_value: str | None
        """
        mod_path = "drain_swamp.konkey.patch_pyproject_reading.ReadPyproject.update"
        if isinstance(mixed_target, Mapping):
            mixed_target.update(d_other)
        else:
            # Parent is a list[dict[str, typing.Any]].
            #    Update dict
            if is_module_debug:  # pragma: no cover
                msg_info = f"In {mod_path}, key / value: {key_name} / {key_value}"
                log.info(msg_info)
            else:  # pragma: no cover
                pass

            # Check for match. If no match append.
            is_found = False
            for idx, d_item in enumerate(mixed_target):
                is_match = d_item.get(key_name, "") == key_value
                if is_match:
                    if is_module_debug:  # pragma: no cover
                        msg_info = f"In {mod_path}, match found: idx {idx} {d_item}"
                        log.info(msg_info)
                    else:  # pragma: no cover
                        pass

                    is_found = True
                    d_item.update(d_other)
                    mixed_target[idx] = d_item
                else:  # pragma: no cover
                    pass

            if not is_found:
                mixed_target.append(d_other)
            else:  # pragma: no cover
                pass

            if is_module_debug:  # pragma: no cover
                msg_info = f"In {mod_path}, after update: {mixed_target}"
                log.info(msg_info)
            else:  # pragma: no cover
                pass


class ReadPyprojectStrict(ReadPyprojectBase):
    """Confine data fields to acceptable by setuptools_scm._config.Configuration."""

    def update(
        self,
        d_target,
        d_other,
        key_name: str | None = None,
        key_value: str | None = None,
    ):
        """Confine to only setuptools_scm._config.Configuration data fields.

        Parent cannot be a ``list[dict]``.

        :param d_target: parent dict
        :type d_target: dict[str, typing.Any]
        :param d_other: dict. Update parent
        :type d_other: dict[str, typing.Any]
        :param key_name: Default None. Ignored
        :type key_name: str | None
        :param key_value: Default None. Ignored
        :type key_value: str | None
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
