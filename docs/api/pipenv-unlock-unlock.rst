pipenv-unlock unlock
=====================

From .in files, creates .unlock files

In ``pyproject.toml``, update dynamic dependencies and optional-dependencies.

Normal usage
-------------

.. code-block:: shell

   pipenv-unlock unlock --dir ci/

Example results
-----------------

Creates the ``.lock`` files in their respective folders

And voila!

Excerpt from ``pyproject.toml``

.. code-block:: text

   [tool.setuptools.dynamic]
   # @@@ editable may_the_force_be_with_you_tshirt\n
   dependencies = { file = ["requirements/prod.unlock"] }
   optional-dependencies.pip = { file = ["requirements/pip.unlock"] }
   optional-dependencies.pip_tools = { file = ["requirements/pip-tools.unlock"] }
   optional-dependencies.ui = { file = ["requirements/ui.unlock"] }
   optional-dependencies.test = { file = ["requirements/test.unlock"] }
   optional-dependencies.dev = { file = ["requirements/dev.unlock"] }
   optional-dependencies.manage = { file = ["requirements/manage.unlock"] }
   optional-dependencies.docs = { file = ["docs/requirements.unlock"] }
   # @@@ end\n

   version = {attr = "[your package]._version.__version__"}

If only one snippet_co in a file, will guess. If many snippets will need
to supply snippet_co (via \-\-snip)

Exit codes
-----------

0 -- Evidently sufficient effort put into unittesting. Job well done, beer on me!

1 -- Unused. Reason: too generic

2 -- Path not a folder

3 -- path given for config file either not a file or not read write

4 -- pyproject.toml config file parse issue. Use validate-pyproject on it then try again

5 -- Backend not supported. Need to add support for that backend. Submit an issue

6 -- The pyproject.toml depends on the requirements folders and files. Create them

7 -- For locking dependencies, pip-tools package must be installed. Not installed

8 -- The snippet is invalid. Either nested snippets or start stop token out of order. Fix the snippet then try again

9 -- In pyproject.toml, there is no snippet with that snippet code

Command options
-----------------

.. csv-table:: :code:`pipenv-unlock unlock` options
   :header: cli, default, description
   :widths: auto

   "-p/--path", "cwd", "absolute path to package base folder"
   "-r/--required", "None", "target and relative to --path, required dependencies .in file. Can be used multiple times"
   "-o/--optional", "None", "target and relative to --path, optional dependencies .in file. Can be used multiple times"
   "-d/--dir", "", "Additional folder(s), not already known implicitly, containing .in files. A relative_path. Can be used multiple times"
   "-k/--kind", "None", "version string kind: now (alias of current), current, tag, or explicit semantic version"
   "-s/--snip", "None", "Snippet code, within a file, unique id of an editable region, aka snippet. Only necessary if multiple snippets"
