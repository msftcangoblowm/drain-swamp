Getting started
================

Requirements files
-------------------

Optional dependencies are broken into lots and lots of requirements which
are interlinked, e.g:

.. code:: text

   requirements/pins.lock
   requirements/pip.in
   requirements/pip-tools.in
   requirements/dev.in
   requirements/kit.in
   requirements/mypy.in
   requirements/manage.in
   requirments/prod.in
   requirments/tox.in
   docs/requirements.in

An author only apply constraints in the most dire circumstances. This
happens only within ``pins.lock``

Although should be obvious, it's not stated often enough; ``*.in`` files
should only contains top level (direct package) dependencies.

.. code:: text

   requirements/pins.lock        # included by others
   requirements/pip.in           # requirements/pip.lock
   requirements/pip-tools.in     # requirements/pip-tools.lock
   requirements/dev.in           # requirements/dev.lock
   requirements/kit.in           # requirements/kit.lock
   requirements/mypy.in          # requirements/mypy.lock
   requirements/manage.in        # requirements/manage.lock
   requirments/prod.in           # requirments/prod.lock and also included by others
   requirments/tox.in            # requirments/tox.lock
   docs/requirements.in          # docs/requirements.lock

Then link this to your ``pyproject.toml`` file

.. code:: text

   [build-system]
   requires = ["setuptools>=69.0.2", "wheel", "build", "setuptools_scm>=8"]
   build-backend = "setuptools.build_meta"

   [project]
   dynamic = [
       "optional-dependencies",
       "dependencies",
       "version",
   ]

   [tool.setuptools.dynamic]
   # @@@ editable may_the_force_be_with_you_tshirt\n
   dependencies = { file = ["requirements/prod.lock"] }
   optional-dependencies.pip = { file = ["requirements/pip.lock"] }
   optional-dependencies.pip_tools = { file = ["requirements/pip-tools.lock"] }
   optional-dependencies.ui = { file = ["requirements/ui.lock"] }
   optional-dependencies.test = { file = ["requirements/test.lock"] }
   optional-dependencies.dev = { file = ["requirements/dev.lock"] }  # includes test.lock
   optional-dependencies.manage = { file = ["requirements/manage.lock"] }
   optional-dependencies.docs = { file = ["docs/requirements.lock"] }  # many sphinx distro packages required
   # @@@ end\n

   version = {attr = "[your package]._version.__version__"}

   [tool.pipenv-unlock]
   folders = [
       "ci",
   ]

   required = { target = "prod", relative_path = "requirements/prod.in" }

   # underscore: hyphen
   optionals = [
       { target = "pip", relative_path = "requirements/pip.in" },
       { target = "pip_tools", relative_path = "requirements/pip-tools.in" },
       { target = "dev", relative_path = "requirements/dev.in" },
       { target = "manage", relative_path = "requirements/manage.in" },
       { target = "docs", relative_path = "docs/requirements.in" },
   ]

Each and every package author might not have a clue a dependency has a
vulnerability and if the end user chooses to use a ``downgrade`` version
they should be able to do so.

Package authors create ``.in`` file. The ``.lock`` are produced by
:command:`pipenv_lock lock --snip=[snippet code]`

Details
--------

``pins.lock``

.. code:: text

   # strictyaml --> python-dateutil --> prod.pip
   # python -m piptools compile does not see this postrelease. Instead chooses python-dateutil-2.8.2
   python-dateutil==2.9.0.post0

**Or**

Manually edit the .lock files. Only after discovering which
causes the dependency conflict.

Created two packages, each with strictyaml as a dependency.
:code:`piptools compile` chose ``python-dateutil-2.8.2`` for one and
``python-dateutil-2.9.0.post0`` for the other

For pip users, welcome to dependency hell!

``dev.in``

.. code:: text

   -c pins.lock
   -c prod.in

   black
   blackdoc
   isort
   flake8
   flake8-pyproject
   mypy
   coverage
   twine
   validate-pyproject

``prod.in``

.. code:: text

   -c pins.lock

   typing-extensions  # backporting latest greatest typing features
   strictyaml         # yaml spec subset validate and parse
   appdirs            # Adhere to XDG spec
   attrs

``dev.in``

.. code:: text

   # strictyaml --> python-dateutil --> prod.pip
   # python -m piptools compile does not see this postrelease. Instead chooses python-dateutil-2.8.2
   python-dateutil==2.9.0.post0

   typing-extensions  # backporting latest greatest typing features
   strictyaml         # yaml spec subset validate and parse
   appdirs            # Adhere to XDG spec
   attrs

   black
   blackdoc
   isort
   flake8
   flake8-pyproject
   mypy
   coverage
   twine
   validate-pyproject

Meaning it's KISS and not compiled. This is what setuptools and pip understands.

Again the ``pins.lock`` file is only for really really bad situations where
a package author had no choice but to step in.

This issue, actually, is better handled by the end user using :command:`uv`
with ``--override`` option, rather than hardcoding a constraint.
