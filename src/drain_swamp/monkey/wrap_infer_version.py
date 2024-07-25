"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

``pyproject.toml``

.. code-block:: text

   [project.entry-points."setuptools.finalize_distribution_options"]
   drain_swamp = "drain_swamp.monkey.wrap_infer_version:infer_version"

infer_version sets the dist.metadata.version. Would like to do more ...

.. seealso::

   `[alter Distribution object] <https://setuptools.pypa.io/en/latest/userguide/extension.html#customizing-distribution-options>`_

   Command and sub-command classes
   https://setuptools.pypa.io/en/latest/userguide/extension.html#customizing-commands

.. code-block:: text

   setuptools_scm._integration.setuptools.infer_version
     _config.Configuration.from_file
     _assign_version

.. seealso::

   https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_integration/setuptools.py
   https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_integration/pyproject_reading.py
   https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_config.py
   https://github.com/pypa/setuptools_scm/blob/main/src/setuptools_scm/_get_version_impl.py
   https://github.com/pypa/setuptools/blob/e9f0be98ea4faaba4a7b2d07ba994a81fde8f42f/setuptools/build_meta.py#L161

   https://github.com/pypa/setuptools/issues/2491
   https://github.com/pypa/setuptools/discussions/4083
   https://github.com/pypa/setuptools/issues/3896#issuecomment-1656714771

   SOLUTIONS

   - pass config_settings through backend
     https://github.com/pypa/setuptools/commit/fc95b3b83d6d5b561dc0a356995edf4c99785a6f

   - throw away setup.cfg file
     https://github.com/pypa/setuptools/issues/3896#issuecomment-1708513197

     .. code-block:: shell

        export DIST_EXTRA_CONFIG=/tmp/setuptools-build.cfg
        echo -e '[build_ext]\nparallel = 8\n[bdist_wheel]\npy_limited_api = cp311' > $DIST_EXTRA_CONFIG
        python -m build


"""

import logging
import os
from pathlib import Path

import drain_swamp.monkey.plugins as package_plugins

from .hooks.manager import (  # noqa: F401
    after,
    before,
    get_plugin_manager,
)
from .patch_pyproject_reading import ReadPyproject

log = logging.getLogger("drain_swamp.monkey.wrap_infer_version")

__all__ = ("run_build_plugins",)


def _get_config_settings():
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
    msg_warn = (
        "Expected env variable, DS_CONFIG_SETTINGS. Should contain "
        "path to .toml file. File contains project.name, project.version, "
        "tool.config-settings.kind and tool.config-settings.set-lock"
    )
    toml_path = os.environ.get("DS_CONFIG_SETTINGS", None)
    if toml_path is not None:
        path_f = Path(toml_path)
        is_exists = path_f.exists() and path_f.is_file()
        if is_exists:
            """Attempt to read toml file. section tool.config-settings.
            Get all key/value pairs
            """
            try:
                pyproj_data = ReadPyproject()(path=path_f, tool_name="config-settings")
            except LookupError:
                d_section = {}
                log.warning(msg_warn)
            else:
                # from setuptools_scm._integration.toml import TOML_RESULT
                d_section = pyproj_data.section

                # No config settings. Log warning
                if len(d_section.keys()) == 0:
                    log.warning(msg_warn)
                else:  # pragma: no cover
                    pass

        else:  # pragma: no cover
            d_section = {}
    else:  # pragma: no cover
        d_section = {}

    return d_section


def inspect_pm(pm) -> None:  # pragma: no cover
    """Determine which plugin implementations match the spec

    :param pm: Plugin manager instance
    :type pm: pluggy.PluginManager

    .. seealso::

       https://pluggy.readthedocs.io/en/latest/#inspection
    """
    mod_path = "drain_swamp.monkey.wrap_infer_version:inspect_pm"

    wo_specs = []
    for name in pm.hook.__dict__.items():
        if name[0] != "_":
            # : HookCaller
            hook = getattr(pm.hook, name[0])
            msg_info = (
                f"{mod_path} hook.get_hookimpls {name[0]} -> {hook.get_hookimpls()}"
            )
            log.info(msg_info)
            if not hook.has_spec():
                wo_specs.append(name)
    msg_info = f"{mod_path} wo spec hooks {wo_specs}"
    log.info(msg_info)


def run_build_plugins(d_config_settings):
    """Run build plugins. The plugins are responsible for user input
    validation and choosing which user input is of interest

    :param d_config_settings:

       config settings dict. What normally would be supplied as
       :code:`python -m build` config setting cli options

    :type d_config_settings: collections.abc.Mapping[str, typing.Any]
    """
    mod_path = "drain_swamp.monkey.wrap_infer_version:run_build_plugins"
    # Can register more pluggy specs with _register_hooks
    # If positional arg not a types.ModuleType raises TypeError
    pm = get_plugin_manager(package_plugins)

    # Very useful check to see if specs fcn names match hook fcn names
    # raises pluggy.PluginValidationError
    # pm.check_pending()
    pass

    # https://pluggy.readthedocs.io/en/latest/api_reference.html#pluggy.PluginManager.add_hookcall_monitoring
    # undo = pm.add_hookcall_monitoring(before, after)
    pass

    result_lst_before = pm.hook.ds_before_version_infer(
        config_settings=d_config_settings
    )
    result_lst_on = pm.hook.ds_on_version_infer(config_settings=d_config_settings)
    result_lst_after = pm.hook.ds_after_version_infer(config_settings=d_config_settings)

    # print hook results. Group by hook spec. Plugins executed in order
    if len(result_lst_before) != 0:  # pragma: no cover
        str_msgs = "\n".join(result_lst_before)
        msg = f"{mod_path} plugin version_infer (before): {str_msgs}"
        log.warning(msg)

    if len(result_lst_on) != 0:  # pragma: no cover
        str_msgs = "\n".join(result_lst_on)
        msg = f"{mod_path} plugin version_infer (on): {str_msgs}"
        log.warning(msg)

    if len(result_lst_after) != 0:  # pragma: no cover
        str_msgs = "\n".join(result_lst_after)
        msg = f"{mod_path} plugin version_infer(after): {str_msgs}"
        log.warning(msg)

    # undo()
    pass


def infer_version(dist):
    """Sets the dist.metadata.version

    Would also like to:

    - get cmdline options -C--kind and -C--set-lock
    - refresh_links
    - write to  version_file. kind: tag, current, now, and version str

    In ``pyproject.toml``

    .. code-block:: text

       [project.entry-points."setuptools.finalize_distribution_options"]
       drain_swamp = "drain_swamp.monkey.wrap_infer_version:infer_version"

    :param dist: API interface for interacting with setuptools
    :type dist: setuptools.Distribution

    .. todo:: remove restriction

       _req_links/backend.py should be refactored use the plugins

    .. seealso::

       ``_req_links/backend.py``

    """
    # In the future, remove this restriction
    dist_name = dist.metadata.name
    is_drain_swamp = dist_name is not None and dist_name == "drain_swamp"
    if is_drain_swamp:  # pragma: no cover
        return
    else:  # pragma: no cover
        pass

    # Until setuptools implements passing config-settings into subprocess
    d_config_settings = _get_config_settings()

    run_build_plugins(d_config_settings)
