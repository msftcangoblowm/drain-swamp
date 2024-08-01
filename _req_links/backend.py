"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Generate the .lnk files. Do not change the lock/unlock state

Usage

.. code-block:: shell

   python -m build -C--set-lock=0 --sdist
   python -m build -C--set-lock=0 -C--kind="tag" --sdist
   python -m build -C--set-lock=1 -C--kind="0.5.2" --sdist
   python -m build -C--set-lock=0 -C--kind="current" --sdist
   python -m build -C--set-lock=0 -C--kind='dog food tastes better than this' --sdist

   python -m --no-deps dist/[pck].whl

.. note:: imports work how?!

   In ``pyproject.toml`` section [build-system], :code:`backend-path=[".", "src"]`
   ``src/`` folder gets appended to the :code:`sys.path`

.. note:: BackendType subclasses

   Must be imported, after BackendType. This registers them

.. seealso::

   `in-tree backend <https://setuptools.pypa.io/en/latest/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks>`_

   `pep660 <https://peps.python.org/pep-0660/>`_

   https://github.com/pypa/setuptools_scm/blob/main/_own_version_helper.py

"""

from __future__ import annotations

import copy
import sys
from collections.abc import Mapping

from setuptools import build_meta as _orig
from setuptools.build_meta import *  # noqa: F401 F403

from drain_swamp.monkey.wrap_infer_version import (
    _get_config_settings,
    run_build_plugins,
)


def get_requires_for_build_sdist(config_settings=None):
    """Before building package, runs plugins:

    - create/refresh .lnk files
    - set the version

    config_settings keys

    set-lock

    - 1 -- .lnk --> .lock

    - 0 -- .lnk --> .unlock

    kind

    tag, now, current, or a version str

    Usage

    .. code-block:: shell

       python -m build -C--set-lock=1 -C--kind="0.5.2" --sdist --verbose
       python -m build --config-setting="--set-lock=1" --config-setting="--kind=0.5.2" --verbose

    .. note:: setuptools_scm

       setuptools_scm hook occurs after our plugins. Would brutishly and
       clumsly to overwrite the version.

       Remove pyproject.toml [tool.setuptools_scm] section

       setuptools_scm generates WARNINGs w/ tracebacks; can be safely ignored

    .. note::

       :code:`python -m build` runs within a subprocess exit codes always 1

    """
    mod_path = "_req_links/backend.py"

    # Document usage and echo raw user input
    msg_info = (
        "-C--set-lock=1 to lock dependencies.\n"
        "-C--set-lock=0 to unlock dependencies.\n"
        "If not provided, looks at pyproject.toml lock state"
    )
    print(msg_info)

    msg_info = (
        """-C--kind empty gets exit code 8\n"""
        """-C--kind="current" gets current scm version. Writes\n"""
        """-C--kind="tag" gets version from version file\n"""
        """-C--kind="0.0.1" forces build a particular version\n"""
        "If not provided, same as tag"
    )
    print(msg_info)

    msg_info = f"INFO {mod_path} config_settings: {config_settings!r}"
    print(msg_info)

    if config_settings is None or not isinstance(config_settings, Mapping):
        # tox does not pass in config_settings, check DS_CONFIG_SETTINGS
        d_config_settings_tox = _get_config_settings()
        if d_config_settings_tox is not None:
            d_config_settings = copy.deepcopy(d_config_settings_tox)
        else:
            msg_exc = (
                "ERROR In build backend, expecting config_settings to be "
                f"Mapping got {config_settings!r} "
            )
            print(msg_exc)
            exit_code = 8
            sys.exit(exit_code)
    else:  # pragma: no cover
        d_config_settings = copy.deepcopy(config_settings)

    run_build_plugins(d_config_settings)

    return _orig.get_requires_for_build_sdist(d_config_settings)
