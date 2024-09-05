"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: __all__
   :type: tuple[str]
   :value: ("BackendSetupTools",)

   Module's exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

from __future__ import annotations

import logging
import os

from .backend_abc import BackendType
from .constants import g_app_name

__package__ = "drain_swamp"
__all__ = ("BackendSetupTools",)

_logger = logging.getLogger(f"{g_app_name}.backend_abc")


class BackendSetupTools(BackendType):
    """Support for setuptools.

    Create an instance using the factory,
    :py:meth:`drain_swamp.backend_abc.BackendType.load_factory`

    Can read in the relevant ``pyproject.toml`` section for dependencies
    and optional-dependencies, another section details extras, and then
    rewrite the editable section

    The editable section should look like

    When dependency locked

    .. code-block:: text

       # @@@ editable
       dependencies = { file = ["requirements/prod.lock"] }
       optional-dependencies.pip = { file = ["requirements/pip.lock"] }
       optional-dependencies.pip_tools = { file = ["requirements/pip-tools.lock"] }
       optional-dependencies.dev = { file = ["requirements/dev.lock"] }
       optional-dependencies.manage = { file = ["requirements/manage.lock"] }
       optional-dependencies.docs = { file = ["docs/requirements.lock"] }
       # @@@ end

       version = {attr = "logging_strict._version.__version__"}

    When not dependency locked

    .. code-block:: text

       # @@@ editable
       dependencies = { file = ["requirements/prod.unlock"] }
       optional-dependencies.pip = { file = ["requirements/pip.unlock"] }
       optional-dependencies.pip_tools = { file = ["requirements/pip-tools.unlock"] }
       optional-dependencies.dev = { file = ["requirements/dev.unlock"] }
       optional-dependencies.manage = { file = ["requirements/manage.unlock"] }
       optional-dependencies.docs = { file = ["docs/requirements.unlock"] }
       # @@@ end

       version = {attr = "logging_strict._version.__version__"}

    Other ``pyproject.toml`` dynamic properties are not placed within
    the editable section

    In pyproject.toml,

    .. code-block:: text

       [tool.pipenv-unlock]
       extras = [
           "pip",
           "pip_tools",  # <-- underscore
           "dev",
           "manage",
           "docs",
       ]
       required = "requirements/prod.in"
       optionals = [
           "requirements/prod.in",
           "requirements/pip.in",
           "requirements/pip-tools.in",  # <-- hyphen
           "requirements/dev.in",
           "requirements/manage.in",
           "docs/requirements.in",
       ]

    - extras

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

      ``optional-dependencies.pip_tools = { file = ["requirements/pip-tools.unlock"] }``

      The file stem is hyphen but the dependency contains underscores

    .. py:attribute:: BACKEND_NAME
       :type: str
       :value: "setuptools"

       This backend driver is setuptools

    .. py:attribute:: PYPROJECT_TOML_SECTION_NAME
       :type: str
       :value: "tool.setuptools.dynamic"

       Dynamic section

       Not supported:

       - setup.cfg
       - setup.py
       - pyproject.toml, but not dynamic

       An editable section is created by start and end tokens. So not
       needed to know the name of the section. Left here for completeness

    :ivar d_pyproject_toml: pyproject.toml in one giant dict
    :vartype d_pyproject_toml: dict[str, typing.Any]
    :ivar path_config: Absolute path to pyproject.toml file
    :vartype path_config: pathlib.Path
    :ivar required:

       Default None. From cli, relative path to required dependencies .in file

    :vartype required: tuple[str, pathlib.Path] | None
    :ivar optionals:

       Default empty tuple. relative path of optional dependency ``.in`` files

    :vartype optionals: dict[str, pathlib.Path]
    :ivar parent_dir:

           folder path If provided and acceptable overrides attr, path_config

    :vartype parent_dir: pathlib.Path | None

    :raises:

       - :py:exc:`FileNotFoundError` -- package required dependency file is required

    """

    BACKEND_NAME = "setuptools"
    PYPROJECT_TOML_SECTION_NAME = "tool.setuptools.dynamic"

    def __init__(
        self,
        d_pyproject_toml,
        path_config,
        required=None,
        optionals={},
        parent_dir=None,
        additional_folders=(),
    ):
        """Class constructor."""
        super().__init__()
        self._path_config = path_config

        # may raise: FileNotFoundError
        self.load(
            d_pyproject_toml,
            required=required,
            optionals=optionals,
            parent_dir=parent_dir,
            additional_folders=additional_folders,
        )

    @property
    def backend(self):
        """Get Backend name.

        :returns: Backend name
        :rtype: str
        """
        cls = type(self)
        return cls.BACKEND_NAME

    def compose_dependencies_line(self, suffix):
        """Compose required dependency line.

        .. code-block:: text

           dependencies = { file = ["requirements/prod.lock"] }

        In this case,
        required is ``requirements/prod.in``
        suffix is ``.lock`` or ``lock`` or ``.unlock`` or ``unlock``

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :returns: tool.setuptools.dynamic dependencies line
        :rtype: collections.abc.Iterator[str]
        """
        _logger.info(f"path_required: {self.required} {type(self.required)}")
        if self.required is None:
            yield from ()
        else:
            # tuple[str, Path]
            target, path_required_abs = self.required
            path_rel = path_required_abs.relative_to(self.parent_dir)
            path_dir = path_rel.parent

            str_suffix = self.fix_suffix(suffix)

            # file stem contains hyphens, not underscores
            stem = path_rel.stem
            stem = stem.replace("_", "-")

            path_dir_final = path_dir.joinpath(f"{stem}{str_suffix}")

            ret = f"""dependencies = {{ file = ["{path_dir_final}"] }}"""

            yield ret

        yield from ()

    def compose_optional_lines(self, suffix):
        """Compose the optional lines returning an Iterator.

        Optional lines are in this format

        .. code-block:: text

           optional-dependencies.pip_tools = { file = ["requirements/pip-tools.unlock"] }

        In this case,

        - suffix is ``.unlock``
        - extra is ``pip_tools``
        - optional is ``requirements/pip-tools.in``

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :returns: tool.setuptools.dynamic dependencies and optional-dependencies lines
        :rtype: collections.abc.Iterator[str]
        """
        for target, path_abs in self.optionals.items():
            path_rel = path_abs.relative_to(self.parent_dir)
            str_suffix = self.fix_suffix(suffix)
            # file stem contains hyphens, not underscores
            path_rel_r = path_rel.parent
            stem_r = path_rel.stem
            stem_r = stem_r.replace("_", "-")
            path_full_r = path_rel_r.joinpath(f"{stem_r}{str_suffix}")

            target_l = target.replace("-", "_")
            ret = (
                f"""optional-dependencies.{target_l} = {{ file = ["""
                f""""{str(path_full_r)}"] }}"""
            )
            yield ret

        yield from ()

    def compose(self, suffix):
        """Create the new contents to be placed into the snippet.
        ``pyproject.toml`` required and optional-dependencies.

        :param suffix: File suffix. Either ``.lock`` or ``.unlock``
        :type suffix: str
        :returns: tool.setuptools.dynamic dependencies and optional-dependencies lines
        :rtype: str
        """
        super().compose()  # do validation checks
        ret = []
        ret.extend(list(self.compose_dependencies_line(suffix)))
        ret.extend(list(self.compose_optional_lines(suffix)))
        sep = os.linesep
        lines = sep.join(ret)

        return lines


BackendType.register(BackendSetupTools)
