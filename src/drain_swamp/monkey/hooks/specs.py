"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

config_settings dict would normally contain cli args passed thru by

.. code-block:: text

   python -m build -C--[option name]="[value]"

However setuptools has not implemented support for this. The build
process hooks are each ran in a subprocess. :code:`sys.argv` is not
modified to pass thru the config settings. As a temporary workaround,
**that doesn't add functionality**, a temporary config file is created
and an environment variable containing path to the temporary config file
is passed to :code:`python -m build`

.. code-block:: shell

   export DS_CONFIG_SETTINGS=/tmp/setuptools-build.toml
   cat <<-EOF > "$DS_CONFIG_SETTINGS"
   [project]
   name = "whatever"
   version = "99.99.99a1.dev6"

   [tool.config-settings]
   kind="0.0.1"
   set-lock="0"
   EOF
   python -m build --no-isolation

The above is a valid pyproject.toml file. Neither name nor version have
any meaning. In section tool.config-settings, all key/value pairs are
str; cli command options are always str

.. seealso::

   `pluggy toy example <https://pluggy.readthedocs.io/en/latest/#a-toy-example>`_

   `pytest specs <https://github.com/pytest-dev/pytest/blob/main/src/_pytest/hookspec.py>`_

   `kedro specs <https://github.com/kedro-org/kedro/blob/main/kedro/framework/hooks/specs.py>`_

.. py:data:: hook_spec

   py:func:`pluggy.HookspecMarker` variable

"""

from __future__ import annotations

from typing import Any

import pluggy

from .constants import HOOK_NAMESPACE

hook_spec = pluggy.HookspecMarker(HOOK_NAMESPACE)


@hook_spec
def ds_before_version_infer(config_settings: dict[str, Any]) -> str | None:
    """Hook invoked, after gathering build environment packages and before
    any build requires packages execute their hooks

    So for example, if ``setuptools-scm`` is in build-system.requires,
    it's hooks are executed after drain-swamp hooks. This is
    counter-intuitive, a pleasent surprise, and known only thru experience

    :param config_settings:

        Dict containing cli args which should have been passed thru
        by :code:`python -m build -C--[option name]="[value]"`, but isn't

        So a workaround is used until setuptools can add support

    :type config_settings: dict[str, typing.Any]
    """


@hook_spec
def ds_on_version_infer(config_settings: dict[str, Any]) -> str | None:
    """Hook invoked, after gathering build environment packages. As the scm version

    :param config_settings:

       Dict containing cli args which should have been passed thru
       by :code:`python -m build -C--[option name]="[value]"`, but isn't

       So a workaround is used until setuptools can add support

    :type config_settings: dict[str, typing.Any]
    """


@hook_spec
def ds_after_version_infer(config_settings: dict[str, Any]) -> str | None:
    """Hook invoked, after gathering build environment packages.

    :param config_settings:

       Dict containing cli args which should have been passed thru
       by :code:`python -m build -C--[option name]="[value]"`, but isn't

       So a workaround is used until setuptools can add support

    :type config_settings: dict[str, typing.Any]
    """
