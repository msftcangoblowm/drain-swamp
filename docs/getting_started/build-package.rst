Build a package
================

Python packaging is slowly evolving. To all agree on **the** way
forward, together, a PEP is needed.

The issue
----------

When :code:`python -m build` runs, the build front end calls the build
backend in a subprocess. Somewhere along the way, neglected to clearly
specify how to pass arguments along so they are available within the subprocess.

We are in that weird interm period. Waiting for a PEP to appear so **open**
discussions on how to handle this situation can occur

How to
-------

If setuptools worked as expected, this would be the build command

.. code-block:: shell

   python -m build -C--kind="1.0.0" -C--set-lock="0"

This would build the package with version 1.0.0 and dependencies unlocked.

Good news and bad news

The good news is this works for building drain-swamp

Bad news is all other packages will need to use an interm workaround.

Create an environment variable holding the absolute path to a ``.toml`` file
containing the config_settings

.. code-block:: shell

   export DS_CONFIG_SETTINGS=/tmp/setuptools-build.toml
   cat <<-EOF > "$DS_CONFIG_SETTINGS"
   [project]
   name = "whatever"
   version = "99.99.99a1.dev6"

   [tool.config-settings]
   kind="1.0.0"
   set-lock="0"
   EOF
   python -m build

The project section is so the ``.toml`` file is valid.

Note all user input, from the command line, **are** str. So within the
``.toml``, only str data type is acceptable

Build process walk through
---------------------------

*If techno babble is not your thing or will lead to a brain hemorrhage, skip this section*

:code:`python -m build` calls setuptools, which delegates to a build
front end, within a subprocess calls a build back end, neglects to
pass thru the command line arguments, and finally drain-swamp.

Which is left scratching it's head thinking, but but but where are the
command line arguments (aka config_settings)?

For now, it's accessible by looking for the environment variable,
``DS_CONFIG_SETTINGS``, and from there the ``.toml`` file.

If not found, the entire build process will exit, with an explanation
exactly how to resolve the issue.

If found, drain-swamp plugin manager runs build plugins. That deals
with the package version and creating/refreshing dependency locks symlink

After drain-swamp, setuptools-scm stuff runs, since, in our
``pyproject.toml``, there is no [tool.setuptools-scm] section,
setuptools-scm version stuff is not run.

The setuptools-scm file finders does not require [tool.setuptools-scm]
section and therefore is run.

Your build plugins
-------------------

Learn how to write a (build) plugin

Check out the `pluggy [docs] <https://pypi.org/project/pluggy/>`_
`[example] <https://pluggy.readthedocs.io/en/latest/#the-plugin>`_

plugin specs, ``drain_swamp.monkey.hooks.specs``

.. code-block:: text

   - ds_before_version_infer(config_settings: dict[str, typing.Any]) -> str | None:

   - ds_on_version_infer(config_settings: dict[str, typing.Any]) -> str | None:

   - ds_after_version_infer(config_settings: dict[str, typing.Any]) -> str | None:

These plugin hooks indicates to the plugin manager when to run your plugin.

When plugins are run revolves around when the package version is set. before on or after.

For example, the refresh dependency locks symlink plugin runs, *before*. Cuz
it's package version agnostic (doesn't care one way or the other)
