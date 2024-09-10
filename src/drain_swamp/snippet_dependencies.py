"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: __all__
   :type: tuple[str]
   :value: ("SnippetDependencies",)

   Module's exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

from __future__ import annotations

import logging
from pathlib import PurePosixPath

from .constants import g_app_name
from .exceptions import MissingRequirementsFoldersFiles

__package__ = "drain_swamp"
__all__ = ("SnippetDependencies",)

_logger = logging.getLogger(f"{g_app_name}.snippet_dependencies")


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


def _check_are_requirements_files(in_files):
    """Check there are dependency requirements files.

    Which every Python package will have.

    :param in_files: Dependency requirements ``.in`` files
    :type in_files: collections.abc.Sequence[pathlib.Path]
    :raises:

        - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
          No requirements folders and files. Abort and provide user feedback

    """

    is_empty = len(in_files) == 0
    if is_empty:
        msg_exc = "There are no requirements folders and files. Prepare these"
        raise MissingRequirementsFoldersFiles(msg_exc)


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
        _logger.info(f"path_required: {self._required} {type(self._required)}")
        if self._required is None:
            yield from ()
        else:
            # tuple[str, Path]
            target, path_required_abs = self._required
            path_rel = PurePosixPath(path_required_abs).relative_to(
                PurePosixPath(self._parent_dir),
            )
            path_dir = path_rel.parent

            # file stem contains hyphens, not underscores
            stem = path_rel.stem
            stem = stem.replace("_", "-")

            path_dir_final = path_dir.joinpath(f"{stem}{suffix}")

            # TOML format -- paths use single quote, not double quote
            ret = f"""dependencies = {{ file = ['{path_dir_final}'] }}"""

            yield ret

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
            path_rel = PurePosixPath(path_abs).relative_to(
                PurePosixPath(self._parent_dir),
            )

            # file stem contains hyphens, not underscores
            path_rel_r = path_rel.parent
            stem_r = path_rel.stem
            stem_r = stem_r.replace("_", "-")
            path_full_r = path_rel_r.joinpath(f"{stem_r}{suffix}")

            target_l = target.replace("-", "_")
            # TOML format -- paths use single quote, not double quote
            ret = (
                f"""optional-dependencies.{target_l} = {{ file = ["""
                f"""'{str(path_full_r)}'] }}"""
            )
            yield ret

        yield from ()

    def __call__(self, suffix, parent_dir, gen_in_files, required, optionals):
        """Create the new contents to be placed into the snippet.
        ``pyproject.toml`` required and optional-dependencies.

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :param parent_dir: Folder absolute path
        :type parent_dir: pathlib.Path
        :param gen_in_files: dependency requirements ``.in`` file absolute paths
        :type gen_in_files: collections.abc.Generator[pathlib.Path, None, None]
        :param required:

           Default None. From cli, relative path to required dependencies .in file

        :type required: tuple[str, pathlib.Path] | None
        :param optionals:

           Default empty tuple. relative path of optional dependency ``.in`` files

        :type optionals: dict[str, pathlib.Path]
        :returns: tool.setuptools.dynamic dependencies and optional-dependencies lines
        :rtype: str
        :raises:

            - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
              No requirements folders and files. Abort and provide user feedback

        """
        self._parent_dir = parent_dir
        self._required = required
        self._optionals = optionals

        str_suffix = _fix_suffix(suffix)

        in_files = list(gen_in_files)
        # May raise MissingRequirementsFoldersFiles
        _check_are_requirements_files(in_files)

        ret = []
        ret.extend(list(self._compose_dependencies_line(str_suffix)))
        ret.extend(list(self._compose_optional_lines(str_suffix)))
        # TOML format line endings **MUST** be \n, not \r\n
        sep = "\n"
        lines = sep.join(ret)

        return lines
