"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Provides primitives to use hooks to extend behaviour

Built-in plugins are lazy loaded. Args must be passed in using a workaround

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

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("_create_hook_manager", "hook_impl")

   This sub-package exports

.. seealso::

   Example plugins specs and implementation

   - `kedro <https://docs.kedro.org/en/latest/hooks/introduction.html>`_

"""

from .manager import _create_hook_manager
from .markers import hook_impl

__all__ = (
    "_create_hook_manager",
    "hook_impl",
)
