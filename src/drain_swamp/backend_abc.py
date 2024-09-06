"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

pep518 backends support ABC

Assumes package:

- uses ``pyproject.toml`` to store static packaging info. Especially not ``setup.cfg``.
  ``setup.py`` usage should be limited to C code and semantic versioning integration

- Not supporting py38-. Removes any justification for prefering
  ``setup.cfg`` or ``setup.py``

- python version isn't locked. e.g. ``requires-python = "~=3.9"``

.. py:data:: __all__
   :type: tuple[str]
   :value: ("BackendType",)

   Module's exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Flag to turn on module level logging

.. py:data:: entrypoint_name
   :type: str
   :value: "pipenv-unlock"

   Entrypoint name. For access to settings in ``pyproject.toml``

"""

from __future__ import annotations

import abc
import logging
import platform
import sys
from pathlib import (
    Path,
    PurePath,
    PurePosixPath,
    PureWindowsPath,
)
from typing import (
    TYPE_CHECKING,
    ClassVar,
    cast,
)
from unittest.mock import MagicMock

from ._repr import (
    repr_dict_str_path,
    repr_path,
    repr_set_path,
)
from .check_type import (
    is_iterable_not_str,
    is_ok,
    is_relative_required,
)
from .constants import (
    SUFFIX_IN,
    SUFFIX_LOCKED,
    SUFFIX_SYMLINK,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import (
    BackendNotSupportedError,
    MissingRequirementsFoldersFiles,
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
from .parser_in import TomlParser

if sys.version_info >= (3, 9):  # pragma: no cover
    from collections.abc import Sequence
else:  # pragma: no cover
    from typing import Sequence

__package__ = "drain_swamp"
__all__ = ("BackendType",)

_logger = logging.getLogger(f"{g_app_name}.backend_abc")

is_module_debug = False

# taken from pyproject.toml
entrypoint_name = "pipenv-unlock"  # noqa: F401


def try_dict_update(
    set_both,
    path_config,
    target_x,
    path_relative_x,
    is_bypass=False,
):
    """Helper to add absolute paths into pass by reference set.

    ``pyproject.toml`` then cli. cli has higher priority

    :param set_both: pass by reference set. Changed in-place
    :type set_both: dict[str, pathlib.Path]
    :param path_config: base folder absolute path
    :type path_config: pathlib.Path
    :param target_x: target for relative path
    :type target_x: str
    :param path_relative_x: a relative path
    :type path_relative_x: pathlib.Path
    :param is_bypass: Default False. Should be a bool. Bypass exists and file check
    :type is_bypass: typing.Any | None
    """
    if is_bypass is None or not isinstance(is_bypass, bool):
        is_bypass = False
    else:  # pragma: no cover
        pass

    is_relative = is_relative_required(path_relative=path_relative_x)
    if is_relative:
        if not is_bypass:
            path_abs = path_config.joinpath(path_relative_x)
            is_file = path_abs.exists() and path_abs.is_file()
            if is_file:
                set_both.update({target_x: path_abs})
            else:  # pragma: no cover
                pass
        else:
            path_abs = path_config.joinpath(path_relative_x)
            set_both.update({target_x: path_abs})
    else:  # pragma: no cover
        pass


def get_optionals_cli(
    d_both,
    path_config,
    optionals,
):
    """Check sequence of relative paths, to a set, add absolute path(s).

    Helper to make testing possible

    :param d_both: target and absolute paths
    :type d_both: dict[str, pathlib.Path]
    :param path_config: absolute path folder
    :type path_config: pathlib.Path
    :param optionals:

       Preferably relative path contains Path or str. Check type and
       whether path is relative, exists, and is a file

    :type optionals: dict[str, typing.Any]
    """
    is_dict = optionals is not None and isinstance(optionals, dict)
    if is_dict:
        for target, opt in optionals.items():
            if opt is None:
                pass
            else:
                is_pathlike = isinstance(opt, str) or issubclass(type(opt), PurePath)
                if is_pathlike:
                    # supported types
                    path_opt = Path(opt)
                    try_dict_update(d_both, path_config, target, path_opt)
                else:  # pragma: no cover
                    # unsupported type
                    pass
        else:
            # empty sequence
            pass
    else:  # pragma: no cover
        pass


def get_optionals_pyproject_toml(
    d_both,
    d_pyproject_toml,
    path_config,
    is_bypass=False,
):
    """Get options from [tool.pipenv-unlock] optionals.

    dict key / value is target / relative path

    Change the rel path into an absolute path

    :param d_both: updated in-place. key / value --> target / absolute path
    :type d_both: dict[str, pathlib.Path]
    :param d_pyproject_toml: pyproject.toml dict
    :type d_pyproject_toml: dict[str, typing.Any]
    :param path_config: absolute folder path
    :type path_config: pathlib.Path
    :param is_bypass: Default False. True checks if file exists
    :type is_bypass: bool | None
    """
    if is_bypass is None or not isinstance(is_bypass, bool):
        is_bypass = False

    d_tool = d_pyproject_toml.get("tool", {}).get(entrypoint_name, {})
    for key, mixed_blob in d_tool.items():
        is_optionals = (
            key == "optionals"
            and mixed_blob is not None
            and isinstance(mixed_blob, Sequence)
        )
        if is_module_debug:  # pragma: no cover
            _logger.info(f"is_optionals: {is_optionals}")
        else:  # pragma: no cover
            pass

        if is_optionals:
            for d_optional_dependency in mixed_blob:
                if "target" in d_optional_dependency.keys():
                    target = d_optional_dependency["target"]
                else:  # pragma: no cover
                    target = None

                if "relative_path" in d_optional_dependency.keys():
                    opt = d_optional_dependency["relative_path"]
                else:  # pragma: no cover
                    opt = None

                is_missing_expected_keys = target is None or opt is None
                if is_missing_expected_keys:  # pragma: no cover
                    """a dict, but no recognized keys. Expected target
                    and relative_path"""
                    continue
                else:  # pragma: no cover
                    pass

                is_pathlike = isinstance(opt, str) or issubclass(type(opt), PurePath)
                if is_module_debug:  # pragma: no cover
                    msg_info = f"is_pathlike: {is_pathlike}"
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass

                if is_pathlike:
                    path_opt = Path(opt)
                    if is_module_debug:  # pragma: no cover
                        msg_info = f"target / rel path: {target} / {path_opt}"
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass

                    try_dict_update(
                        d_both,
                        path_config,
                        target,
                        path_opt,
                        is_bypass=is_bypass,
                    )
                else:  # pragma: no cover
                    # unsupported type
                    pass
            else:
                # empty sequence
                pass
        else:  # pragma: no cover
            pass


def get_required_pyproject_toml(
    d_pyproject_toml,
    path_config,
    is_bypass=False,
):
    """From pyproject.toml [tool.pipenv-unlock], get ``required`` value.
    Which is a dict

    is_bypass controls whether it must already exist or not. Useful for testing

    :param d_pyproject_toml: pyproject.toml dict
    :type d_pyproject_toml: dict[str, typing.Any]
    :param path_config: absolute folder path
    :type path_config: pathlib.Path
    :param is_bypass: Default False. True checks if file exists
    :type is_bypass: bool | None
    :returns: tuple containing required target and abs path
    :rtype: tuple[str, pathlib.Path] | None
    """
    if is_bypass is None or not isinstance(is_bypass, bool):
        is_bypass = False

    ret = None
    d_tool = d_pyproject_toml.get("tool", {}).get(entrypoint_name, {})
    for key, mixed_blob in d_tool.items():
        is_required = (
            key == "required"
            and mixed_blob is not None
            and isinstance(mixed_blob, dict)
        )
        if is_module_debug:  # pragma: no cover
            _logger.info(f"is_required: {is_required}")
        else:  # pragma: no cover
            pass

        if is_required:
            is_target = "target" in mixed_blob.keys()
            is_relative_path = "relative_path" in mixed_blob.keys()
            if is_module_debug:  # pragma: no cover
                _logger.info(f"is_target (pyproject.toml): {is_target}")
                _logger.info(f"is_relative_path (pyproject.toml): {is_relative_path}")
            else:  # pragma: no cover
                pass
            if is_target and is_relative_path:
                target_b = cast(str, mixed_blob["target"])
                path_rel_b = cast(str, mixed_blob["relative_path"])
                # assumes default extensions
                is_relative = is_relative_required(path_relative=Path(path_rel_b))
                if is_module_debug:  # pragma: no cover
                    _logger.info(f"is_relative (pyproject.toml): {is_relative}")
                else:  # pragma: no cover
                    pass
                if is_relative:
                    path_abs = path_config.joinpath(path_rel_b)
                    if is_bypass:
                        ret = (target_b, path_abs)
                    else:
                        is_file = path_abs.exists() and path_abs.is_file()
                        if is_module_debug:  # pragma: no cover
                            _logger.info(f"is_file (pyproject.toml): {is_file}")
                        else:  # pragma: no cover
                            pass
                        if is_file:
                            ret = (target_b, path_abs)
                        else:
                            # not a file
                            ret = None
                else:  # pragma: no cover
                    # unexpected absolute path
                    pass
            else:  # pragma: no cover
                """dict does not contain both target and relative_path
                keys and respective values"""
                pass
        else:  # pragma: no cover
            # in pyproject.toml [tool.pipenv-unlock], no required key nor dict value
            pass

    return ret


def get_required_cli(
    path_config,
    required=None,
    is_bypass=False,
):
    """Process required field provided by cli.

    :param path_config: absolute folder path
    :type path_config: pathlib.Path
    :param required: required package dependencies provided by cli
    :type required: tuple[str, typing.Any] | None
    :param is_bypass: Default False. True checks if file exists
    :type is_bypass: bool | None
    :returns:

       None if no suitable pair otherwise target and abs path

    :rtype: tuple[str, pathlib.Path] | None
    """
    if is_bypass is None or not isinstance(is_bypass, bool):
        is_bypass = False

    ret = None
    if required is not None and is_iterable_not_str(required):
        target_a, path_a = required
        if is_ok(path_a):
            # Check path ok
            is_relative = is_relative_required(path_relative=Path(path_a))
            if is_relative:
                path_abs = path_config.joinpath(path_a)
                if is_bypass:
                    ret = (target_a, path_abs)
                else:
                    is_file = path_abs.exists() and path_abs.is_file()
                    if is_file:
                        ret = (target_a, path_abs)
                    else:  # pragma: no cover
                        # not a file
                        pass
            else:  # pragma: no cover
                # unexpected absolute path
                pass
        elif issubclass(type(path_a), PurePath):
            is_relative = is_relative_required(path_relative=path_a)
            if is_relative:
                path_abs = path_config / path_a
                if is_bypass:
                    ret = (target_a, path_abs)
                else:
                    is_file = path_abs.exists() and path_abs.is_file()
                    if is_file:
                        ret = (target_a, path_abs)
                    else:  # pragma: no cover
                        # not a file
                        pass
            else:  # pragma: no cover
                # unexpected absolute path
                pass
        else:  # pragma: no cover
            # cli required path is unsupported type; do nothing
            pass
    else:
        pass

    return ret


def folders_implied_init(
    parent_dir,
    optionals,
    required=None,
):
    """Determine implied folders.

    Set of relative paths to folders containing ".in" files

    Determined from these properties:

    - type[BackendType].required
    - type[BackendType].optionals

    :param parent_dir: absolute path to parent folder
    :type parent_dir: pathlib.Path
    :param optionals: optional dependencies. target / absolute path
    :type optionals: dict[str, pathlib.Path]
    :param required: Default None. required dependencies. target / absolute path
    :type required: tuple[str, Path] | None
    :returns: set of **relative paths** to folders containing ``.in`` files
    :rtype set[pathlib.Path]
    """
    set_folders_implied = set()
    if required is not None:
        target_a, abs_path_a = required
        path_relative_a = abs_path_a.relative_to(parent_dir)
        path_rel_dir_a = path_relative_a.parent
        if path_rel_dir_a != Path("."):
            set_folders_implied.add(path_rel_dir_a)
        else:  # pragma: no cover
            pass
    else:  # pragma: no cover
        pass

    for target_b, abs_path_b in optionals.items():
        path_relative_b = abs_path_b.relative_to(parent_dir)
        path_rel_dir_b = path_relative_b.parent
        if path_rel_dir_b != Path("."):
            set_folders_implied.add(path_rel_dir_b)
        else:  # pragma: no cover
            pass

    return set_folders_implied


def folders_additional_init(
    parent_dir,
    folders_implied,
    additional_folders=(),
):
    """Determine additional folders, excluding those implied by dependencies.

    Cannot be determined solely from the dependencies or
    optional-dependences. These additional requirements are typically for:

    - tox

    - mypy

    - CI/CD

    In ``pyproject.toml``,

    .. code-block:: text

       [tool.setuptools.dynamic]
       # @@@ editable little_shop_of_horrors_shrine_candles
       dependencies = { file = ["requirements/prod.lock"] }
       optional-dependencies.pip = { file = ["requirements/pip.lock"] }
       optional-dependencies.pip_tools = { file = ["requirements/pip-tools.lock"] }
       optional-dependencies.dev = { file = ["requirements/dev.lock"] }
       optional-dependencies.manage = { file = ["requirements/manage.lock"] }
       optional-dependencies.docs = { file = ["docs/requirements.lock"] }
       # @@@ end

       [tool.pipenv-unlock]
       folders = [
           "docs",
           "requirements",
           "ci",
       ]

       required = { target = "prod", relative_path = "requirements/prod.in" }


       optionals = [
           { target = "pip", relative_path = "requirements/pip.in" },
           { target = "pip_tools", relative_path = "requirements/pip-tools.in" },
           { target = "dev", relative_path = "requirements/dev.in" },
           { target = "manage", relative_path = "requirements/manage.in" },
           { target = "docs", relative_path = "docs/requirements.in" },
       ]

    The implied folders are determined from:

    - tool.pipenv-unlock.required
    - tool.pipenv-unlock.optionals

    In this case, the implied folders are: :code:`{"requirements", "docs"}`

    tool.pipenv-unlock.folders contains the additional folder: :code:`{"ci"}`

    :param parent_dir: absolute path to parent folder
    :type parent_dir: pathlib.Path
    :param folders_implied: Relative path of folders that contain ``.in`` files
    :type folders_implied: set[pathlib.Path]
    :param additional_folders:

       Relative path of additional folders that contain ``.in`` files

    :type additional_folders: tuple[pathlib.Path]
    :returns: set of **relative paths** to additional folders that contain ``.in`` files
    :rtype set[pathlib.Path]
    """
    set_folders_additional = set()
    for path_mixed in additional_folders:
        # click may resolve Path --> str
        if isinstance(path_mixed, str):
            path_mixed = Path(path_mixed)
        else:  # pragma: no cover
            pass

        if path_mixed.is_absolute():
            if (
                path_mixed.exists()
                and path_mixed.is_dir()
                and path_mixed.is_relative_to(parent_dir)
            ):
                path_relative_c = path_mixed.relative_to(parent_dir)
                # folders_implied contains relpath
                is_additional = path_relative_c not in folders_implied
                if path_relative_c != Path(".") and is_additional:
                    set_folders_additional.add(path_relative_c)
                else:  # pragma: no cover
                    # same as parent dir
                    pass
            else:  # pragma: no cover
                # doesn't exist, or not a folder, or not relative to parent folder
                pass
        else:
            abs_path_c = parent_dir / path_mixed
            # folders_implied contains relpath
            is_additional = path_mixed not in folders_implied
            if abs_path_c.exists() and abs_path_c.is_dir() and is_additional:
                set_folders_additional.add(path_mixed)

    return set_folders_additional


def ensure_folder(val):
    """Ensure arg is a folder.

    :param val:

       Preferrable a Path. Can be either a file or a folder. We want the folder

    :type val: typing.Any
    :returns: A folder Path
    :rtype: pathlib.Path
    :raises:

       - :py:exc:`NotADirectoryError` -- BackendType.path_config
         is neither a file nor a folder

    """
    msg_exc = "Expecting a file or a folder path. Received something else"
    path_v = None
    if val is None:
        path_val = None
    else:
        if isinstance(val, MagicMock):
            # For testing only. Expect the return_value to be a Path
            path_v = val.return_value
            if issubclass(type(val.return_value), PurePath):
                path_val = path_v
            else:  # pragma: no cover
                pass
        elif issubclass(type(val), PurePath):
            path_val = val
        else:
            path_val = None

    # Two birds one stone
    if path_val is None:
        # None or a MagicMock.return_value which is not a Path
        msg_exc = f"Unsupported type got {type(val)}"
        raise TypeError(msg_exc)
    else:  # pragma: no cover
        pass

    if path_val.is_file() and not path_val.is_symlink():
        ret = path_val.parent
    elif path_val.is_dir() and not path_val.is_symlink():
        ret = path_val
    else:
        """symlink, is junction (Windows only), socket, fifo,
        block device, or char device"""
        raise NotADirectoryError(msg_exc)

    return ret


class BackendType(abc.ABC):
    """ABC of packaging backend support.

    get_registered and __subclasshook__ makes this ABC aware of all subclasses

    All that is required is to import this ABC and all subclasses

    To create a subclass backend instance, call
    :py:meth:`drain_swamp.backend_abc.BackendType.load_factory`.

    The backend is known immediately after reading in ``pyproject.toml``
    and the appropriate subclass is chosen and instanciated
    """

    _path_required: tuple[str, Path] | None
    _paths_optional: dict[str, Path]
    _path_config: Path
    _parent_dir: Path
    _folders_implied: set[Path]
    _folders_additional: set[Path]
    BACKEND_NAME: ClassVar[str]
    PYPROJECT_TOML_SECTION_NAME: ClassVar[str]

    @staticmethod
    def load_factory(
        path_config,
        required=None,
        optionals={},
        parent_dir=None,
        additional_folders=(),
    ):
        """Choose factory from registered subclasses.

        :param path_config: ``pyproject.toml`` folder path
        :type path_config: pathlib.Path
        :param required: relative path to required dependency .in file
        :type required: tuple[str, pathlib.Path] | None
        :param optionals:

           Default empty tuple. Relative path to optional dependencies
           .in files. There may be some which are not optional dependencies
           like ``requirements/tox.in`` and ``requirements/kit.in``. Which
           are used by CI/CD or tox

        :type optionals: dict[str, pathlib.Path]
        :param parent_dir:

           folder path If provided and acceptable overrides attr, path_config

        :type parent_dir: pathlib.Path | None
        :param additional_folders:

           Default empty Sequence. Folders to search for .in files beyond
           the folders implied by required and optionals relative_path values

        :type additional_folders: tuple[pathlib.Path, ...]
        :returns: Subclass instance
        :rtype: typing.Self
        :raises:

           - :py:exc:`drain_swamp.exceptions.PyProjectTOMLReadError` --
             Either not a file or lacks read permission

           - :py:exc:`drain_swamp.exceptions.PyProjectTOMLParseError` --
             Could not parse pyproject.toml for various reasons

           - :py:exc:`drain_swamp.exceptions.BackendNotSupportedError` --
             No support yet for python package backend

        """

        # During testing, path_config can be cwd, while parent_dir is tmp_path
        if parent_dir is not None and issubclass(type(parent_dir), PurePath):
            path_override = parent_dir
        else:
            path_override = path_config

        if is_module_debug:  # pragma: no cover
            msg_info = (
                "drain_swamp.backend_abc.BackendType:load_factory "
                f"path_override {path_override!r}"
            )
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        # May raise PyProjectTOMLParseError or PyProjectTOMLReadError
        d_pyproject_toml, path_f = TomlParser.read(path_override)

        str_backend = BackendType.determine_backend(d_pyproject_toml)
        lst_registered = list(BackendType.get_registered())

        ret = None
        for kls in lst_registered:
            if kls.BACKEND_NAME == str_backend:
                ret = kls(  # type: ignore[call-arg]
                    d_pyproject_toml,
                    path_f,
                    required=required,
                    optionals=optionals,
                    parent_dir=parent_dir,
                    additional_folders=additional_folders,
                )
            else:  # pragma: no cover
                # continue
                pass

        if ret is None:
            backends_name = [kls.BACKEND_NAME for kls in lst_registered]
            msg_exc = (
                f"No support yet for python package backend {str_backend}. "
                f"Registered backends: {backends_name}. The pyproject.toml "
                f"{path_override}, specify backend in build-system.build-backend "
                "or override tool.pipenv-unlock.wraps-build-backend"
            )
            raise BackendNotSupportedError(msg_exc)
        else:  # pragma: no cover
            pass

        return ret

    def load(
        self,
        d_pyproject_toml,
        required=None,
        optionals={},
        parent_dir=None,
        additional_folders=(),
    ):
        """Called by subclass to process both cli and ``pyproject.toml`` values.

        :param d_pyproject_toml: pyproject.toml dict
        :type d_pyproject_toml: dict[str, typing.Any],
        :param required:

           Default None. Required dependency relative path to .in file. If exists and
           is a file will override pyproject.toml respective value

        :type required: tuple[str, pathlib.Path] | None
        :param optionals:

           Default empty dict. Relative path to optional dependencies
           ``.in`` files. There may be some which are not optional dependencies
           like ``requirements/tox.in`` and ``requirements/kit.in``. Which
           are used by CI/CD or tox

        :type optionals: dict[str, pathlib.Path]
        :param parent_dir:

           folder path If provided and acceptable overrides attr, path_config

        :type parent_dir: pathlib.Path | None
        :param additional_folders:

           Default empty Sequence. Folders to search for .in files beyond
           the folders implied by required and optionals relative_path values

        :type additional_folders: tuple[pathlib.Path, ...]
        """

        # May raise NotADirectoryError, if path_config is neither a file or a folder
        # AND parent_dir not provided
        self.parent_dir = parent_dir

        # path_required Path
        t_c = BackendType.get_required(
            d_pyproject_toml,
            self._parent_dir,
            required=required,
        )
        if t_c is None:
            # Package has no requires
            self._path_required = None
        else:
            self._path_required = t_c

        #    file extension assumed to be .in``
        #    There being no optionals is strange, *but* not an error
        self._paths_optional = BackendType.get_optionals(
            d_pyproject_toml,
            self.parent_dir,
            optionals,
        )

        # _folders_implied
        self._folders_implied = folders_implied_init(
            self.parent_dir,
            self.optionals,
            required=required,
        )

        # _folders_additional
        self._folders_additional = folders_additional_init(
            self.parent_dir,
            self.folders_implied,
            additional_folders=additional_folders,
        )
        #    Annoying to make a unittest just for this property
        assert self.folders_additional == self._folders_additional

    @staticmethod
    def determine_backend(d_pyproject_toml):
        """If a thin-wrapped custom build backend, must specify build backend.

        .. code-block:: text

           [tool.pipenv-unlock]
           wraps-build-backend = "setuptools.build_meta"

        Example custom build backend

        .. code-block:: text

           [build-system]
           requires = ["setuptools>=70.0.0", "wheel", "build", "setuptools_scm>=8"]
           build-backend = "_req_links.backend"
           backend-path = [
               ".",
               "src",
           ]

        :param d_pyproject_toml: ``pyproject.toml`` read in as a dict
        :type d_pyproject_toml: dict[str, typing.Any]
        :returns:

           backend package name. Up to first period. e.g.
           setuptools.build_meta --> "setuptools"

        :rtype: str

        .. seealso::

           https://setuptools.pypa.io/en/latest/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks

        """
        str_build_system = (
            d_pyproject_toml.get("tool", {})
            .get("pipenv-unlock", {})
            .get("wraps-build-backend", None)
        )

        if str_build_system is None:
            # build-backend not thin-wrapped
            d_build_system = d_pyproject_toml.get("build-system", {})
            str_build_system = d_build_system["build-backend"]
        else:  # pragma: no cover
            pass

        str_build = str_build_system.split(".")[0]
        ret = cast(str, str_build)

        return ret

    @staticmethod
    def get_required(
        d_pyproject_toml,
        path_config,
        required=None,
    ):
        """From pyproject.toml, retrieve which required dependencies.

        cli priority over pyproject.toml

        :param d_pyproject_toml: ``pyproject.toml`` read in as a dict
        :type d_pyproject_toml: dict[str, typing.Any]
        :param path_config: absolute path to a folder
        :type path_config: pathlib.Path
        :param required:

           Default None. ``.in`` file path. Contents are the required dependencies

        :type required: tuple[str, typing.Any] | None
        :returns:

           None if no suitable pair otherwise target and abs path

        :rtype: tuple[str, pathlib.Path] | None
        """
        ret = get_required_pyproject_toml(
            d_pyproject_toml,
            path_config,
            is_bypass=False,
        )
        if is_module_debug:  # pragma: no cover
            _logger.info(f"required (pyproject.toml): {ret}")
        else:  # pragma: no cover
            pass

        # cli priority over pyproject.toml
        ret_cli = get_required_cli(
            path_config,
            required,
        )
        if is_module_debug:  # pragma: no cover
            _logger.info(f"required (cli): {ret_cli}")
        else:  # pragma: no cover
            pass

        if ret_cli is not None:
            ret = ret_cli
        else:  # pragma: no cover
            # pyproject.toml supplied required
            pass

        if is_module_debug:  # pragma: no cover
            _logger.info(f"required (final): {ret}")
        else:  # pragma: no cover
            pass

        return ret

    @staticmethod
    def get_optionals(
        d_pyproject_toml,
        path_config,
        optionals,
    ):
        """Combined cli and pyproject.toml optionals. Does not check relative path(s).

        cli supplements ``pyproject.toml``, not overrides completely

        :param d_pyproject_toml: ``pyproject.toml`` read in as a dict
        :type d_pyproject_toml: dict[str, typing.Any]
        :param path_config: absolute path to a folder
        :type path_config: pathlib.Path
        :param optionals: hopefully sequence of relative paths
        :type optionals: dict[str, typing.Any]
        :returns: tuple of paths absolute paths
        :rtype: dict[str, pathlib.Path]
        """
        if TYPE_CHECKING:
            dict_pairs: dict[str, Path]

        dict_pairs = {}

        # pyproject.toml tool.[package name].optionals
        get_optionals_pyproject_toml(
            dict_pairs,
            d_pyproject_toml,
            path_config,
        )

        # cli priority over pyproject.toml
        get_optionals_cli(
            dict_pairs,
            path_config,
            optionals,
        )

        return dict_pairs

    @property
    @abc.abstractmethod
    def backend(self):
        """Get the backend. This is extracted from ``pyproject.toml``.

        :returns: pep518 backend
        :rtype: str
        """
        ...

    @property
    def path_config(self):
        """Path to config file.

        :returns: Path to config file
        :rtype: pathlib.Path
        """
        return self._path_config

    @property
    def parent_dir(self):
        """Override folder Path. Likely a temp folder.

        :returns: Path override folder
        :rtype: pathlib.Path
        """
        return self._parent_dir

    @parent_dir.setter
    def parent_dir(
        self,
        parent_dir=None,
    ):
        """Path config is supposed to be the folder containing ``pyproject.toml``.

        It's unclear. Could be either a file or a folder.

        Sometimes prefer to override the folder location and this
        what parent_dir is intended for.

        :param parent_dir:

           Default None. A folder, often a temp folder, that overrides
           :py:attr:`BackendType.path_config <drain_swamp.backend_abc.BackendType.path_config>`

        :type parent_dir: pathlib.Path
        :raises:

           - :py:exc:`NotADirectoryError` -- BackendType.path_config
             is neither a file nor a folder

        """

        # Avoid calling ensure_folder if parent_dir is acceptable
        if parent_dir is None:
            # may raise NotADirectoryError
            path_config = self.path_config
            path_dir = ensure_folder(path_config)
            if is_module_debug:  # pragma: no cover
                msg_info = (
                    "path_dir (None) --> self.path_config ("
                    f"{type(self.path_config)}): {path_dir}"
                )
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass
        else:
            if not issubclass(type(parent_dir), PurePath):
                # may raise NotADirectoryError
                path_config = self.path_config
                path_dir = ensure_folder(path_config)
                if is_module_debug:  # pragma: no cover
                    msg_info = (
                        f"BackendType.parent_dir setter. path_dir: {path_dir!r} "
                        f"path config: ({self.path_config!r})"
                    )
                    _logger.info(msg_info)
                else:  # pragma: no cover
                    pass
            else:
                is_abs_dir = parent_dir.is_absolute() and parent_dir.is_dir()
                if is_abs_dir:
                    # override acceptable
                    path_dir = parent_dir
                    if is_module_debug:  # pragma: no cover
                        _logger.info(f"path_dir --> parent_dir: {path_dir}")
                    else:  # pragma: no cover
                        pass
                else:
                    # fallback override rejected may raise NotADirectoryError
                    path_config = self.path_config
                    path_dir = ensure_folder(path_config)

                    if is_module_debug:  # pragma: no cover
                        msg_info = (
                            "path_dir (fallback)--> self.path_config("
                            f"{type(self.path_config)}): {path_dir}"
                        )
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass

        self._parent_dir = path_dir

    @property
    def required(self):
        """Required dependency.

        :returns: dependency name and absolute path
        :rtype: tuple[str, pathlib.Path] | None
        """
        return self._path_required

    @property
    def optionals(self):
        """Absolute paths to optional dependencies ``*.in`` files.
        Some may later not become an extra.

        :returns: optional dependency name and absolute path to ``*.in`` files
        :rtype: dict[str, pathlib.Path]
        """
        return self._paths_optional

    @property
    def folders_implied(self):
        """Relative Path to folders containing requirements ``.in`` files.

        Derived from paths in both required and optional dependencies.

        :returns: Unique set of relative Path to folders
        :rtype: set[pathlib.Path]
        """
        return self._folders_implied

    @property
    def folders_additional(self):
        """Relative Path to additional folders.
        Folders which cannot be derived from required and optional dependencies alone.

        :returns: Unique set of relative Path to folders
        :rtype: set[pathlib.Path]
        """
        return self._folders_additional

    @classmethod
    def __subclasshook__(cls, C):
        """A class wanting to be
        :py:class:`~drain_swamp.backend_abc.BackendType`, minimally requires:

        Properties:

        - file_stem

        - file_name

        - package

        - dest_folder

        Methods:

        - extract

        - as_str -- get for free

        - setup -- get for free

        Then register itself
        :code:`BackendType.register(AnotherBackendClass)` or subclass
        :py:class:`~drain_swamp.backend_abc.BackendType`

        :param C:

           Class to test whether implements this interface or is a subclass

        :type C: typing.Any
        :returns:

           ``True`` implements
           :py:class:`~drain_swamp.backend_abc.BackendType`
           interface or is a subclass. ``False`` not a
           :py:class:`~drain_swamp.backend_abc.BackendType`

        :rtype: bool
        """
        if cls is BackendType:
            methods = ("compose",)

            expected_count = len(methods)
            for B in C.__mro__:
                lst = [True for meth in methods if meth in B.__dict__]
                match_count = len(lst)
                is_same = match_count == expected_count
                if is_same:
                    return True
                else:  # pragma: no cover
                    pass
        else:  # pragma: no cover
            pass
        return NotImplemented  # pragma: no cover Tried long enough with issubclass

    @classmethod
    def get_registered(cls):
        """:py:class:`~drain_swamp.backend_abc.BackendType` abc registry.

        Contains registered classes.

        :returns: Generator of registered classes to abc, BackendType
        :rtype: collections.abc.Iterator[type[typing.Self]]

        .. note:: test howto

           Would have to create a mock with all the abstract properties
           and methods implemented. This is **alot** of work. Testing
           is skipped

        .. note:: :py:func:`abc._get_dump`

           Does exist in :py:mod:`abc`. The module level function is
           protected and not intended to be user facing.

           This is the only way to know which classes are registered to
           support this abc. Would prefer not to hard-code the
           registered classes

        """
        for weakref_cls in abc._get_dump(BackendType)[1]:  # type: ignore
            ref = weakref_cls
            klass = ref()
            if klass is not None:
                yield klass
            else:  # pragma: no cover
                pass

        yield from ()

    @staticmethod
    def fix_suffix(suffix):
        """Prepend period if suffix lacks it.

        :param suffix:

           one file suffix, not suffixes, which might not be prepended by a period

        :type suffix: str
        :returns: Suffix with preceding period character
        :rtype: str
        """
        if not suffix.startswith("."):
            ret = f".{suffix}"
        else:
            ret = suffix

        return ret

    def __repr__(self) -> str:
        """Fallback :py:func:`repr` implementation. For display of the
        instance state, not for recreating an instance.

        :returns: instance state
        :rtype: str
        """
        # Subclass, not the ABC class. backend is implied by the subclass
        cls = type(self)
        is_win = platform.system().lower() == "windows"

        ret = (
            f"<{cls.__name__} "
            f"""{repr_path("path_config", self.path_config)}"""
            f"""{repr_path("parent_dir", self.parent_dir)}"""
            f"""{repr_dict_str_path("optionals", self.optionals)}"""
            f"""{repr_set_path("folders_implied", self.folders_implied)}"""
            f"""{repr_set_path("folders_additional", self.folders_additional)}"""
        )

        t_required = self.required
        if t_required is not None:
            req_name, req_path = t_required
            if is_win:  # pragma: no cover
                req_purepath = PureWindowsPath(req_path)
                ret += f"required=('{req_name!s}', {req_purepath!r})"
            else:  # pragma: no cover
                req_purepath = PurePosixPath(req_path)
                ret += f"required=('{req_name!s}', {req_purepath!r})"
        else:
            # t_required is None when pyproject.toml contains static dependencies
            # Remove <comma><space> token
            ret = ret[:-2]

        ret += ">"

        return ret

    def in_files(self):
        """Create generator of all ``.in`` files.
        For both implied and additional folders.

        :returns: All the ``.in`` files in any of the implied and additional folders
        :rtype: collections.abc.Generator[pathlib.Path, None, None]
        """
        # combine two sets (of absolute paths)
        mod_path = "backend_abc.BackendType.in_files"
        set_folders = self.folders_implied | self.folders_additional
        if is_module_debug:  # pragma: no cover
            _logger.info(f"{mod_path} implied folders: {self.folders_implied}")
            _logger.info(f"{mod_path} additional folders: {self.folders_additional}")
            _logger.info(f"{mod_path} set_folders: {set_folders}")
        else:  # pragma: no cover
            pass

        for rel_path in set_folders:
            if is_module_debug:  # pragma: no cover
                _logger.info(f"{mod_path} rel_path: {rel_path}")
            else:  # pragma: no cover
                pass
            path_dir = self.parent_dir
            abs_path = path_dir.joinpath(rel_path)
            pattern = f"**/*{SUFFIX_IN}"
            if is_module_debug:  # pragma: no cover
                _logger.info(f"{mod_path} abs_path: {abs_path}")
                _logger.info(f"{mod_path} pattern {pattern}")
                _logger.info(f"""{mod_path} files: {list(abs_path.glob(pattern))}""")
            else:  # pragma: no cover
                pass
            yield from abs_path.glob(f"**/*{SUFFIX_IN}")
        yield from ()

    @staticmethod
    def is_locked(path_config):
        """Check package dependency lock state.
        For supported backends. Assuming ``pyproject.toml`` exists.

        :param path_config: absolute path to ``pyproject.toml``
        :type path_config: pathlib.Path
        :returns:

           True if has mostly dependencies and optional dependencies
           have mostly ``.lock`` suffixes otherwise False

           None indicates snippet with that id does not exist

        :rtype: bool
        :raises:

           - :py:exc:`AssertionError` -- in pyproject.toml [tool.setuptools.dynamic]
              section, expect this section and at least key, dependencies

           - :py:exc:`drain_swamp.exceptions.PyProjectTOMLParseError` --
             either not found or cannot be parsed

           - :py:exc:`drain_swamp.exceptions.PyProjectTOMLReadError` --
             Either not a file or lacks read permission

        .. todo:: requirements.txt usage

           pip-compile usage encourages: .in and .txt
           .txt is equivalent to .lock, but .lock meaning is explicit and clear

           drain_swamp broke .txt --> .unlock and .lock

           What if accidently or still using .txt?

        """
        # tomli parser ignores snippet (comments).
        # This is for the best; parsing quotes in regex is too hard
        # Possible to get a snippet from an invalid ``pyproject.toml`` file
        # May raise PyProjectTOMLParseError or PyProjectTOMLReadError
        if is_module_debug:  # pragma: no cover
            msg_info = f"BackendType.is_locked reading path config: {path_config!r}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        try:
            d_pyproject_toml, path_f = TomlParser.read(path_config)
        except (PyProjectTOMLParseError, PyProjectTOMLReadError):
            raise

        if is_module_debug:  # pragma: no cover
            _logger.info(f"BackendType.is_locked d_pyproject_toml: {d_pyproject_toml}")
        else:  # pragma: no cover
            pass

        locks = []
        unlocks = []

        def sorting_hat(relpath: Path) -> None:
            """Decide whether a lock or unlock dependency. Then weight the counts."""
            nonlocal locks
            nonlocal unlocks
            nonlocal path_f

            file_name = relpath.name
            if file_name.endswith(SUFFIX_LOCKED):
                locks.append(relpath)
            elif file_name.endswith(SUFFIX_UNLOCKED):
                unlocks.append(relpath)
            elif file_name.endswith(SUFFIX_SYMLINK):
                # resolve symlink gets the file towhich it points
                abspath_package = path_f.parent
                abspath_dependency_file = abspath_package / relpath
                path_resolved = abspath_dependency_file.resolve()

                dependency_file_name = path_resolved.name
                if dependency_file_name.endswith(SUFFIX_LOCKED):
                    locks.append(path_resolved)
                elif dependency_file_name.endswith(SUFFIX_UNLOCKED):
                    unlocks.append(path_resolved)
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                pass

        def choose_winner() -> bool:
            """Choose winner.

            Assumes suffixes are either: .unlock or .lock

            A file suffix of ``.txt`` is not supported

            :returns: True is locked otherwise False
            :rtype: bool
            """
            nonlocal locks
            nonlocal unlocks

            locks_count = len(locks)
            unlocks_count = len(unlocks)

            is_both_zero = locks_count == 0 and unlocks_count == 0
            if is_both_zero:  # pragma: no cover
                # both 0 ! Yikes!! No locks means is unlocked. Even if no unlocks
                ret = False
            else:
                is_locks_win = locks_count != 0
                if is_locks_win:
                    # locked
                    ret = True
                else:
                    # Not locked, so False
                    ret = False

            return ret

        section_ = (
            d_pyproject_toml.get("tool", {}).get("setuptools", {}).get("dynamic", {})
        )
        is_no_tool_setuptools_dynamic_section = len(section_.keys()) == 0

        required_count = 0
        for target, d_ in section_.items():
            if target == "dependencies":
                # required dependencies
                files = d_.get("file", [])
                for f_relpath in files:
                    required_count += 1
                    sorting_hat(Path(f_relpath))
            elif target == "optional-dependencies":
                # optional dependencies
                for target_opt, d_opt in section_.items():
                    files = d_opt.get("file", [])
                    for f_relpath in files:
                        sorting_hat(Path(f_relpath))
            else:  # pragma: no cover
                pass

        if is_no_tool_setuptools_dynamic_section or required_count != 1:
            """Minimally a package has one dependencies ``.in`` with
            cooresponding ``.unlock`` and ``.lock``

            .. code-block:: text

               [tool.setuptools.dynamic]
               # @@@ editable little_shop_of_horrors_shrine_candles
               dependencies = { file = ["requirements/prod.unlock"] }
               # @@@ end

            """
            msg_exc = (
                "in pyproject.toml [tool.setuptools.dynamic] section, "
                "expect this section and at least key, dependencies"
            )
            raise AssertionError(msg_exc)

        if is_module_debug:  # pragma: no cover
            _logger.info(f"BackendType.is_locked locks: {locks}")
            _logger.info(f"BackendType.is_locked unlocks: {unlocks}")
        else:  # pragma: no cover
            pass

        ret = choose_winner()

        return ret

    def compose(self):
        """Subclass must make its own implementation and call,
        :code:`super().compose()`.

        Perform sanity checks

        :raises:

            - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
              No requirements folders and files. Abort and provide user feedback

        """
        # Confirm requirements folders and files exist
        gen_files = self.in_files()
        if len(list(gen_files)) == 0:
            msg_exc = "There are no requirements folders and files. Prepare these"
            raise MissingRequirementsFoldersFiles(msg_exc)
