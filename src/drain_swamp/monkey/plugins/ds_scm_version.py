"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Get the scm version and writes it to version_file

.. py:data:: log
   :type: logging.Logger

   Module level logger

.. seealso::

   `kedro hooks <https://docs.kedro.org/en/latest/extend_kedro/plugins.html#hooks>`_
   `define impl <https://docs.kedro.org/en/latest/hooks/introduction.html#define-the-hook-implementation>`_


Alternative implementation -- Same as setuptools_scm version_infer
Raises LookupError if missing pyproject.toml or missing sections tool.drain-swamp and tool.pipenv-unlock

.. code-block:: text

   from setuptools_scm._integration.setuptools import infer_version as _infer_version
   msg_warn = (
       f"{mod_path} drain-swamp plugins not being run! This should be an error "
       "and stop the build"
   )
   log.warning(msg_warn)
   # setuptools_scm._integration.setuptools._assign_version
   # setuptools_scm._config.Configuration.from_file
   with (
       patch(
           "setuptools_scm._integration.setuptools._config._read_pyproject",
           new_callable=MagicMock(wraps=ReadPyprojectStrict),
       ),
       patch(
           "setuptools_scm._config._read_pyproject",
           new_callable=MagicMock(wraps=ReadPyprojectStrict),
       ),
   ):
       # Limited to only setuptools_scm._config.Configuation fields
       _infer_version(dist)


"""

from __future__ import annotations

import logging
import sys
import warnings
from typing import Any

from drain_swamp._package_installed import is_package_installed
from drain_swamp._run_cmd import run_cmd
from drain_swamp._safe_path import (
    fix_relpath,
    resolve_path,
)
from drain_swamp.monkey.config_settings import ConfigSettings
from drain_swamp.monkey.hooks import markers
from drain_swamp.monkey.hooks.constants import HOOK_NAMESPACE

log = logging.getLogger(__name__)


def _kind(config_settings, fallback="tag"):
    """Sanitize kind user input

    :param config_settings: config dict
    :type config_settings: dict[str, typing.Any] | None
    :param fallback: Default "tag". kind default
    :type fallback: str | None
    :returns: kind can be: current, now, tag, or a semantic version str
    :rtype: str
    """
    if fallback is None or not isinstance(fallback, str):
        str_fallback = "tag"
    else:  # pragma: no cover
        str_fallback = fallback

    is_not_dict = config_settings is None or not isinstance(config_settings, dict)
    if is_not_dict:
        ret = str_fallback
    else:
        # config_settings is coming from the cli, values will be str
        try:
            if "--kind" in config_settings.keys():
                ret = config_settings["--kind"]
            elif "kind" in config_settings.keys():
                ret = config_settings["kind"]
            else:
                # Do not use scm version. Version from tool.pipenv-unlock.version_file
                ret = str_fallback

            # whitespace only is invalid --> AssertionError
            assert isinstance(ret, str) and len(ret.strip()) != 0
        except AssertionError:
            msg_warn_invalid_kind = (
                "-C--kind expected to be: tag, current, now, or a "
                f"version str. Got {ret!r}"
            )
            warnings.warn(msg_warn_invalid_kind)
            ret = str_fallback

    return ret


@markers.hook_impl(specname=f"{HOOK_NAMESPACE}_on_version_infer")
def on_version_infer(config_settings: dict[str, Any]) -> str | None:
    """Update version_file depending on kind: current, now, tag,
    semantic version str

    pluggy will inspect this method's signature. So keep it!
    """
    mod_path = "backend plugin ds_scm_version"

    is_installed = is_package_installed("drain_swamp")
    ret = None
    with warnings.catch_warnings(record=True) as w:
        kind = _kind(config_settings)
        if len(w) != 0:
            ret = str(w[0].message)

    log.info(f"{mod_path} kind: {kind!r}")
    config_settings_path = ConfigSettings.get_abs_path()
    log.info(f"{mod_path} config_settings_path: {config_settings_path}")

    if ret is not None:
        return ret
    else:
        if kind in ("current", "now"):
            # Get current version from scm and write to file
            if not is_installed:  # pragma: no cover
                # pep366
                cmd = [
                    sys.executable,
                    fix_relpath("src/drain_swamp/cli_scm_version.py"),
                ]
            else:
                # ../cli_scm_version.py entrypoint
                cmd = [
                    resolve_path("scm-version"),
                ]
            cmd.extend(["get", "--is-write"])
            t_out = run_cmd(cmd, cwd=None)
            out, err, code, subprocess_msg = t_out
            if subprocess_msg is not None:
                ret = None
                warnings.warn(subprocess_msg)
            else:
                # A plugins output should be None if no error occurred
                if code == 0:
                    ret = None
                else:
                    # error occurred
                    if err is None:  # pragma: no cover
                        # on stderr, entrypoint did not provide an explanation
                        # make an adhoc msg
                        ret = f"Exit code: {code} cmd {cmd}"
                    else:
                        # on stderr, entrypoint provided an explanation
                        ret = err
        elif kind == "tag":
            """:code:`python -m build` will use version from
            version_file. Do not change version_file"""
            ret = None
        else:
            # version str
            if not is_installed:  # pragma: no cover
                # pep366
                cmd = [
                    sys.executable,
                    fix_relpath("src/drain_swamp/cli_scm_version.py"),
                ]
            else:
                # ../cli_scm_version.py entrypoint
                cmd = [
                    resolve_path("scm-version"),
                ]
            cmd.extend(["write", kind])
            t_out = run_cmd(cmd, cwd=None)
            out, err, code, subprocess_msg = t_out
            if subprocess_msg is not None:
                ret = None
                warnings.warn(subprocess_msg)
            else:
                # A plugins output should be None if no error occurred
                if code == 0:
                    ret = None
                else:
                    # error occurred
                    if err is None:  # pragma: no cover
                        # on stderr, entrypoint did not provide an explanation
                        # make an adhoc msg
                        ret = f"Exit code: {code} cmd {cmd}"
                    else:
                        # on stderr, entrypoint provided an explanation
                        ret = err

            # for debugging purposes
            # ret = repr(t_out)
            pass

        return ret
