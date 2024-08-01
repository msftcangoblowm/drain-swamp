"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Plugin to refresh dependency lock .lnk files. Which are symlinks to respective
.unlock or .lock file

.. seealso::

   `kedro hooks <https://docs.kedro.org/en/latest/extend_kedro/plugins.html#hooks>`_
   `define impl <https://docs.kedro.org/en/latest/hooks/introduction.html#define-the-hook-implementation>`_

"""

from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import Any

from drain_swamp.backend_abc import BackendType
from drain_swamp.backend_setuptools import BackendSetupTools  # noqa: F401
from drain_swamp.check_type import click_bool
from drain_swamp.exceptions import (
    BackendNotSupportedError,
    MissingRequirementsFoldersFiles,
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
from drain_swamp.lock_toggle import refresh_links
from drain_swamp.monkey.hooks import markers
from drain_swamp.monkey.hooks.constants import HOOK_NAMESPACE

log = logging.getLogger(__name__)


def _is_set_lock(config_settings, default=None):
    """From config, determine should dependencies be locked or unlocked.

    :param config_settings: config dict
    :type config_settings: dict[str, typing.Any] | None
    :param default: Default None. Create symlink to .unlock file
    :type default: Any | None
    :returns: True lock dependencies otherwise keep the dependencies unlocked
    :rtype: bool | None

    .. seealso::

       `click.BOOL <https://click.palletsprojects.com/en/latest/parameters/#parameter-types>`_
       acceptable true and false strings
       “1”, “true”, “t”, “yes”, “y”, and “on”
       “0”, “false”, “f”, “no”, “n”, and “off”

    """
    is_default_ng = default is not None and not isinstance(default, bool)
    if is_default_ng:
        default = None
    else:  # pragma: no cover
        pass

    is_not_dict = config_settings is None or not isinstance(config_settings, dict)
    if is_not_dict:
        # Default is dependency unlocked
        str_set_lock = None
    else:
        if "--set-lock" in config_settings.keys():
            # Not going to setuptools by call to :code:`python -m build`
            str_set_lock = config_settings["--set-lock"]
        elif "set-lock" in config_settings.keys():
            str_set_lock = config_settings["set-lock"]
        else:
            # Default is dependency unlocked
            str_set_lock = None

    # Simulates click.Bool
    ret = click_bool(val=str_set_lock)
    if ret is None:
        ret = default

    return ret


def _parent_dir(config_settings, default=None):
    """A hack just for testing. Into config_settings, add parent-dir.
    Which is to be feed into BackendType.load_factory call

    :param config_settings: config dict
    :type config_settings: dict[str, typing.Any] | None
    :param default: Default False. Create symlink to .unlock file
    :type default: Any | None
    :returns: parent_dir value to be used with BackendType.load_factory
    :rtype: pathlib.Path
    :meta private
    """
    is_default_ng = default is None or not issubclass(type(default), str)
    if is_default_ng:
        default = None
    else:  # pragma: no cover
        default = Path(default)

    is_not_dict = config_settings is None or not isinstance(config_settings, dict)
    if is_not_dict:
        # Default is dependency unlocked
        ret = None
    else:
        if "--parent-dir" in config_settings.keys():
            # Not going to setuptools by call to :code:`python -m build`
            str_ret = config_settings["--parent-dir"]
            ret = Path(str_ret)
        elif "parent-dir" in config_settings.keys():
            str_ret = config_settings["parent-dir"]
            ret = Path(str_ret)
        else:
            # Default is dependency unlocked
            ret = None

    return ret


@markers.hook_impl(tryfirst=True, specname=f"{HOOK_NAMESPACE}_before_version_infer")
def before_version_infer(config_settings: dict[str, Any]) -> str | None:
    """Refresh .lnk files. Symlink which points to respective
    .unlock or .lock files

    Is not dependent on state. Hook implementation can be run early

    pluggy will inspect this method's signature. So keep it!

    :param config_settings: config dict
    :type config_settings: dict[str, typing.Any]
    :raises:

       - :py:exc:`PyProjectTOMLReadError`
       - :py:exc:`PyProjectTOMLParseError`
       - :py:exc:`BackendNotSupportedError`
       - :py:exc:`MissingRequirementsFoldersFiles`
       - :py:exc:`AssertionError`

    """
    mod_path = "backend plugin ds_refresh_links"
    cwd = Path.cwd()
    # If is_set_lock is None, get lock state from pyproject.toml
    is_set_lock = _is_set_lock(config_settings, default=None)
    parent_dir = _parent_dir(config_settings)

    log.info(f"{mod_path} is_set_lock: {is_set_lock} parent_dir {parent_dir}")

    try:
        inst = BackendType.load_factory(cwd, parent_dir=parent_dir)
        log.info(
            f"{mod_path} inst.path_config: {inst.path_config} abs?: {inst.path_config.is_absolute()}"
        )
        refresh_links(inst, is_set_lock=is_set_lock)
    except PyProjectTOMLReadError:
        msg_exc = (
            f"Either not a file or lacks read permissions. {traceback.format_exc()}"
        )
        ret = msg_exc
    except PyProjectTOMLParseError:
        msg_exc = f"Cannot parse pyproject.toml. {traceback.format_exc()}"
        ret = msg_exc
    except BackendNotSupportedError as e:
        """cause typically code neglecting to import backend drivers
        after importing BackendType. Drivers not automatically imported"""
        msg_exc = f"{e} {traceback.format_exc()}"
        ret = msg_exc
    except MissingRequirementsFoldersFiles:
        msg_exc = (
            "Missing requirements folders and files. Prepare these "
            f"{traceback.format_exc()}"
        )
        ret = msg_exc
    except AssertionError:
        msg_exc = (
            "Either no pyproject.toml section, tool.setuptools.dynamic "
            "or no dependencies key"
        )
        ret = msg_exc
    else:
        ret = None

    return ret
