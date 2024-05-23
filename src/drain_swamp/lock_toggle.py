"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Without ``tool.pipenv-unlock.folders``:

   The folders containing .in files is deduced from
   ``[tool.pipenv-unlock]`` ``required`` and ``optionals`` fields. Which contains
   keys: ``target`` and ``relative_path``.

   ``relative_path`` value contains the relative path to a .in file.
   Without dups, use a set, those files' parent folder will contain our .in files.

With ``tool.pipenv-unlock.folders``:

There may be additional folders not implied by required/optionals
(aka ``dependencies`` or ``optional-dependencies``), which contain
``.in`` files.

Example use cases

-  ``ci``
   Used by CI/CD. e.g. mypy.in, tox.in

- ``kit``
  For building tarball and wheels, e.g. kit.in

In which case, there needs to be a way to specify all folders
containing ``.in`` files.

Explicitly specifying all folders is preferred over a derived
(implied) folders list

Example ``pyproject.toml``. specifies an additional folder, ``ci``.

.. code-block:: text

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

.. py:data:: is_piptools
   :type: bool

   pip-compile is installed by package, pip-tools.

   Avoid executing code:`which pip-compile` within a subprocess, by
   checking can import ``piptools``. Then assume package pip-tools,
   install cli commands: :command:`pip-compile` and :command:`pip-sync`

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("lock_compile", "unlock_create")

   Module exports

"""

from __future__ import annotations

import logging
import pkgutil
import subprocess
from pathlib import Path

from .constants import (
    PATH_PIP_COMPILE,
    SUFFIX_LOCKED,
    g_app_name,
)

__package__ = "drain_swamp"
__all__ = (
    "lock_compile",
    "unlock_create",
)

_logger = logging.getLogger(f"{g_app_name}.lock_toggle")


def is_piptools():
    """Check whether package pip-tools is installed. If not the
    :command:`pip-compile` would not be available

    This function is patchable

    :returns: True if pip-tools installed otherwise False
    :rtype: bool
    """
    return pkgutil.find_loader("piptools") is not None


def lock_compile(inst):
    """In a subprocess call :command:pip-compile to create .lock files

    :param inst:

       Backend subclass instance which has folders property containing
       ``collections.abc.Sequence[Path]``

    :type inst: BackendType
    :returns: Generator of abs path to .lock files
    :rtype: collections.abc.Generator[pathlib.Path, None, None]
    :raises:

       - :py:exc:`AssertionError` -- pip-tools is not installed and is
         a dependency of this package

    """
    assert is_piptools()

    # store pairs
    lst_pairs = []

    # Look at the folders. Then convert all ``.in`` --> ``.lock``
    gen_unlocked_files = inst.in_files()

    in_files = list(gen_unlocked_files)
    _logger.info(f"in_files: {in_files}")
    del gen_unlocked_files

    gen_unlocked_files = inst.in_files()
    for path_abs in gen_unlocked_files:
        abspath_locked = path_abs.parent.joinpath(f"{path_abs.stem}{SUFFIX_LOCKED}")
        lst_pairs.append((str(path_abs), str(abspath_locked)))

    _logger.info(f"pairs: {lst_pairs}")

    # Serial it's whats for breakfast
    for in_path, out_path in lst_pairs:
        cmd = (
            str(PATH_PIP_COMPILE),
            "--allow-unsafe",
            "--resolver",
            "backtracking",
            "-o",
            out_path,
            in_path,
        )
        _logger.info(f"cmd: {cmd}")
        subprocess.run(cmd, cwd=inst.parent_dir)
        is_confirm = Path(out_path).exists() and Path(out_path).is_file()
        if is_confirm:
            _logger.info(f"yield: {out_path!s}")
            yield Path(out_path)
        else:
            # File not created. Darn you pip-compile!
            yield from ()

    yield from ()


def unlock_create(inst):
    """pip requirement files can contain both ``-r`` and ``-c`` lines.
    Relative path to requirement files and constraint files respectively.

    Originally thought ``-c`` was a :command:`pip-compile` convention,
    not a pip convention. Opps!

    With presence of both ``.in`` and ``.lock`` files and then using the
    ``.in`` files would imply the package is (dependency) unlocked.

    So ``.in`` files are ``.unlock`` files.

    Creating ``.unlock`` files would serve no additional purpose, besides
    being explicit about the state of the package. That the author probably
    is no longer actively maintaining the package and thus has purposefully
    left the dependencies unlocked.

    :param inst:

       Backend subclass instance which has folders property containing
       ``collections.abc.Sequence[Path]``

    :type inst: BackendType
    """
    pass
