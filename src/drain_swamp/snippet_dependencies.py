"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("SnippetDependencies", "get_required_and_optionals", "generate_snippet")

   Module's exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: is_module_debug
   :type: bool
   :value: False

   turn on/off module level log messages

.. py:class:: T_REQUIRED

.. py:data:: T_REQUIRED
   :type: tuple[str, pathlib.Path] | None
   :noindex:

   Required dependency

.. py:class:: T_OPTIONALS

.. py:data:: T_OPTIONALS
   :type: collections.abc.Mapping[str, pathlib.Path]
   :noindex:

   Optional dependencies

"""

import logging
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import (
    Path,
    PurePath,
)
from typing import (
    Union,
    cast,
)

from ._safe_path import resolve_joinpath
from .constants import (
    SUFFIX_IN,
    SUFFIX_LOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_infile import InFiles
from .lock_util import replace_suffixes_last
from .monkey.patch_pyproject_reading import ReadPyproject
from .pep518_venvs import VenvMapLoader

__package__ = "drain_swamp"
__all__ = (
    "SnippetDependencies",
    "get_required_and_optionals",
    "generate_snippet",
)

_logger = logging.getLogger(f"{g_app_name}.snippet_dependencies")
is_module_debug = False

T_REQUIRED = Union[tuple[str, Path], None]
T_OPTIONALS = Mapping[str, Path]


def _fix_suffix(suffix):
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


class SnippetDependencies:
    """In ``pyproject.toml``, dependencies can be organized in
    many requirements files. So the assumption dependencies are dynamic rather
    than static.

    |project_name| distinguishes between, and has both, dependency lock
    and unlock files.

    Requirement files, typically with ``.txt`` extention, are replaced with:
    ``.in``, ``.unlock``, ``.lock``, and ``.lnk``.

    The ``.unlock`` and ``.lock`` are generated, but can be manually editted.

    The ``.lnk`` is created during package build process. On Windows, it's
    a file copy on other platforms it's a symlink. Python build process
    resolves symlinks.

    A snippet is placed in section, ``tool.setuptools.dynamic``. The snippet
    has both start and end tokens. No need to know the section name.
    The snippet contains both dependencies and optional-dependencies.

    Metadata is needed to generate the snippet contents.

    - (extra) folders
    - required
    - optionals

    When dependency locked (and before refresh)

    .. code-block:: text

       # @@@ editable
       dependencies = { file = ['requirements/prod.lock'] }
       optional-dependencies.pip = { file = ['requirements/pip.lock'] }
       optional-dependencies.pip_tools = { file = ['requirements/pip-tools.lock'] }
       optional-dependencies.dev = { file = ['requirements/dev.lock'] }
       optional-dependencies.manage = { file = ['requirements/manage.lock'] }
       optional-dependencies.docs = { file = ['docs/requirements.lock'] }
       # @@@ end

       version = {attr = 'logging_strict._version.__version__'}

    When not dependency unlocked (and before refresh)

    .. code-block:: text

       # @@@ editable
       dependencies = { file = ['requirements/prod.unlock'] }
       optional-dependencies.pip = { file = ['requirements/pip.unlock'] }
       optional-dependencies.pip_tools = { file = ['requirements/pip-tools.unlock'] }
       optional-dependencies.dev = { file = ['requirements/dev.unlock'] }
       optional-dependencies.manage = { file = ['requirements/manage.unlock'] }
       optional-dependencies.docs = { file = ['docs/requirements.unlock'] }
       # @@@ end

       version = {attr = 'logging_strict._version.__version__'}

    Notice the dynamic version is not within the snippet.

    **Metadata section**

    .. code-block:: text

       [tool.pipenv-unlock]
       folders = [
           "pip",
           "pip_tools",  # <-- underscore
           "dev",
           "manage",
           "docs",
       ]
       required = "requirements/prod.in"
       optionals = [
           'requirements/prod.in',
           'requirements/pip.in',
           'requirements/pip-tools.in',  # <-- hyphen
           'requirements/dev.in',
           'requirements/manage.in',
           'docs/requirements.in',
       ]

    - folders

      There maybe other .in/.lock/.unlock files, such as kit.in and
      tox.in, these are used by tox or CI/CD. These will also need
      .lock and .unlock files

    - required

      Even if the package has no required dependencies,
      .in/.lock/.unlocked files should still exist. By knowing which
      is the required dependencies related files, will know the others
      are optional, besides ``pins[.in|.lock|.unlock]``

    - optionals

      package optional-dependencies

      Can also be provided/overridden by passing in cli options

      Not allow cooresponding ``[.in|.lock|.unlock]`` will be
      optional-dependencies.

      File stems will have hyphens not underscore

      ``optional-dependencies.pip_tools = { file = ['requirements/pip-tools.unlock'] }``

      The file stem is hyphen but the dependency contains underscores

    :raises:

       - :py:exc:`FileNotFoundError` -- package required dependency file is required

    """

    def _compose_dependencies_line(self, suffix):
        """Compose required dependency line.

        .. code-block:: text

           dependencies = { file = ['requirements/prod.lock'] }

        In this case,
        required is ``requirements/prod.in``
        suffix is ``.lock`` or ``lock`` or ``.unlock`` or ``unlock``

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :returns: tool.setuptools.dynamic dependencies line
        :rtype: collections.abc.Iterator[str]
        """
        if is_module_debug:  # pragma: no cover
            msg_info = f"path_required: {self._required} {type(self._required)}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        if self._required is None:
            yield from ()
        else:
            # tuple[str, Path]
            target, path_required_abs = self._required
            is_abspath = PurePath(path_required_abs).is_absolute()
            if is_abspath:
                abspath_f = replace_suffixes_last(path_required_abs, suffix)
                path_rel = PurePath(abspath_f).relative_to(
                    PurePath(self._parent_dir),
                )
                rel_path = path_rel.as_posix()
                # TOML format -- paths use single quote, not double quote
                ret = f"""dependencies = {{ file = ['{rel_path}'] }}"""
                yield ret
            else:  # pragma: no cover
                yield from ()

        yield from ()

    def _compose_optional_lines(self, suffix):
        """Compose the optional lines returning an Iterator.

        Optional lines are in this format

        .. code-block:: text

           optional-dependencies.pip_tools = { file = ['requirements/pip-tools.unlock'] }

        In this case,

        - suffix is ``.unlock``
        - extra is ``pip_tools``
        - optional is ``requirements/pip-tools.in``

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :returns: tool.setuptools.dynamic dependencies and optional-dependencies lines
        :rtype: collections.abc.Iterator[str]
        """
        for target, path_abs in self._optionals.items():
            # Even on Windows, treat as a posix path
            is_abspath = PurePath(path_abs).is_absolute()
            if is_abspath:
                target_l = target.replace("-", "_")

                abspath_f = replace_suffixes_last(path_abs, suffix)
                path_rel = PurePath(abspath_f).relative_to(
                    PurePath(self._parent_dir),
                )
                rel_path = path_rel.as_posix()
                # TOML format -- paths use single quote, not double quote
                ret = (
                    f"""optional-dependencies.{target_l} = {{ file = ["""
                    f"""'{rel_path}'] }}"""
                )
                yield ret
            else:  # pragma: no cover
                yield from ()

        yield from ()

    def __call__(self, suffix, parent_dir, required, optionals):
        """Create the new contents to be placed into the snippet.
        ``pyproject.toml`` required and optional-dependencies.

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :param parent_dir: Folder absolute path
        :type parent_dir: pathlib.Path
        :param required:

           Default None. From cli, relative path to required dependencies .in file

        :type required: tuple[str, pathlib.Path] | None
        :param optionals:

           Default empty tuple. relative path of optional dependency ``.in`` files

        :type optionals: dict[str, pathlib.Path]
        :returns: tool.setuptools.dynamic dependencies and optional-dependencies lines
        :rtype: str
        """
        self._parent_dir = parent_dir

        # Need to check valid absolute paths to requirement files
        self._required = required
        self._optionals = optionals

        str_suffix = _fix_suffix(suffix)

        ret = []
        gen_req = self._compose_dependencies_line(str_suffix)
        for req_line in gen_req:
            ret.append(req_line)

        gen_opt = self._compose_optional_lines(str_suffix)
        for req_line in gen_opt:
            ret.append(req_line)

        # TOML format line endings **MUST** be \n, not \r\n
        sep = "\n"
        lines = sep.join(ret)

        return lines


def get_required_and_optionals(path_cwd, path_f, tool_name=("pipenv-unlock",)):
    """
    :param path_cwd: Project base folder or test base folder
    :type path_cwd: pathlib.Path
    :param path_f: pyproject.toml absolute path
    :type path_f: pathlib.Path
    :param tool_name: pyproject.toml section(s) name
    :type tool_name: str | collections.abc.Sequence[str]
    :returns:

       All dependencies absolute Path, required dependency absolute Path
       or None, Mapping of target and optional dependencies absolute Path

    :rtype: tuple[collections.abc.Sequence[pathlib.Path], drain_swamp.snippet_dependencies.T_REQUIRED, drain_swamp.snippet_dependencies.T_OPTIONALS]
    """
    #    required and optionals
    abspath_ins = []
    d_section = ReadPyproject()(path=path_f, tool_name=tool_name).section
    d_required_raw = d_section.get("required", {})
    # tuple[str, Path] | None
    if isinstance(d_required_raw, Mapping):
        required_relpath = d_required_raw.get("relative_path", None)
        if required_relpath is not None:
            abspath_dest = cast("Path", resolve_joinpath(path_cwd, required_relpath))
            abspath_dest_in = replace_suffixes_last(abspath_dest, SUFFIX_IN)
            t_required = (
                d_required_raw.get("target", ""),
                abspath_dest_in,
            )
            abspath_dest_in.parent.mkdir(parents=True, exist_ok=True)
            abspath_ins.append(abspath_dest_in)
        else:
            t_required = None
    else:  # pragma: no cover
        t_required = None

    d_optionals = {}
    lst_optionals_raw = d_section.get("optionals", [])
    is_seq = lst_optionals_raw is not None and isinstance(lst_optionals_raw, Sequence)
    if is_seq:
        for d_optional_dependency in lst_optionals_raw:
            optstr_target = d_optional_dependency.get("target", None)
            optstr_relpath = d_optional_dependency.get("relative_path", None)
            is_target = (
                optstr_target is not None
                and isinstance(optstr_target, str)
                and len(optstr_target.strip()) != 0
            )
            is_relpath = (
                optstr_relpath is not None
                and isinstance(optstr_relpath, str)
                and len(optstr_relpath.strip()) != 0
            )
            if is_target and is_relpath:
                abspath_dest = cast("Path", resolve_joinpath(path_cwd, optstr_relpath))
                abspath_dest_in = replace_suffixes_last(abspath_dest, SUFFIX_IN)
                abspath_dest_in.parent.mkdir(parents=True, exist_ok=True)
                d_optionals[optstr_target] = abspath_dest_in
                abspath_ins.append(abspath_dest_in)
            else:  # pragma: no cover
                pass
    else:  # pragma: no cover
        pass

    return abspath_ins, t_required, d_optionals


def generate_snippet(
    path_cwd,
    path_config,
    tool_name=("pipenv-unlock",),
    suffix_last=SUFFIX_LOCKED,
):
    """
    :param path_cwd: Project base folder or test base folder
    :type path_cwd: pathlib.Path
    :param path_config: Path to pyproject.toml file
    :type path_config: pathlib.Path
    :param tool_name: pyproject.toml section(s) name
    :type tool_name: str | collections.abc.Sequence[str]
    :param suffix_last: Default ".lock". Last suffix
    :type suffix_last: str
    :returns: Snippet content ready for coping into snippet
    :rtype: str
    :raises:

       - :py:exc:`AssertionError` -- pyproject.toml must be relative to cwd

       - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
         missing dependency support files

       - :py:exc:`ValueError` --

       - :py:exc:`KeyError` -- pyproject section field missing. Cannot retrieve value

    """
    assert path_config.is_relative_to(path_cwd)

    abspath_ins, t_required, d_optionals = get_required_and_optionals(
        path_cwd,
        path_config,
        tool_name=tool_name,
    )

    #    empty folders -- venv base folders. Prevents NotADirectoryError
    loader = VenvMapLoader(path_config.as_posix())
    venv_relpaths = loader.venv_relpaths
    for relpath in venv_relpaths:
        path_dir = cast("Path", resolve_joinpath(path_cwd, relpath))
        path_dir.mkdir(parents=True, exist_ok=True)

    try:
        in_files = InFiles(path_cwd, abspath_ins)
        in_files.resolution_loop()
    except (MissingRequirementsFoldersFiles, ValueError, KeyError):
        raise
    # in_files_count = len(list(in_files.zeroes))

    str_lines_all = SnippetDependencies()(
        suffix_last,
        path_cwd,
        t_required,
        d_optionals,
    )

    # TOML format -- Even on Windows, line seperator must be "\n"
    # if len(str_lines_all) != 0:
    #     lines = str_lines_all.split("\n")
    # else:
    #     lines = []
    return str_lines_all
