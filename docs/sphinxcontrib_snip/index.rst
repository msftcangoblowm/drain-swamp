Sphinx conf.py
===============

Ready to build a package? Will need to update a few things in the user
manual. Used to be tedious, ... but not anymore.

What gets updated?
-------------------

- version

xyz version

- release

Full version str without: epoch, local, and prepended "v"

- release_date

To know when that particular *release* was built

Format: March 15, 2025

- copyright (start year and author name)

Copyright 2024-2025 Dave Faulkmore

Author name is sourced from ``pyproject.toml``

copyright start year has to be provided

How it works
-------------

In ``conf.py``, either ``doc/conf.py`` or ``docs/conf.py``, create a snippet.

Without a snippet_co

.. code-block:: text

   # @@@ editable
   # @@@ end

or with a snippet_co

.. code-block:: text

   # @@@ editable vampire_smoothie_machines
   # @@@ end

Initializing the variables? ... don't even bother; the entire snippet is gonna be replaced

From package base folder,

Without a snippet_co:

.. code-block:: shell

   sphinxcontrib-snip snip

or

With a snippet_co:

.. code-block:: shell

   sphinxcontrib-snip snip --snip=vampire_smoothie_machines

And voila! (look in ``doc?/conf.py``)

.. code-block:: text

   # @@@ editable vampire_smoothie_machines
   copyright = "2023–2024, Dave Faulkmore"
   # The short X.Y.Z version.
   version = "0.0.1"
   # The full version, including alpha/beta/rc tags.
   release = "0.0.1"
   # The date of release, in "monthname day, year" format.
   release_date = "April 25, 2024"
   # @@@ end

Getting Started
-----------------

Have assumed ur package is using ``setuptools-scm``; which talks with git. If
you are hardcoding the version string in a file, stop that. If you
insist on continuing, this extension is not for you.

build-system
"""""""""""""

In ``pyproject.toml``

Minimally, add setuptools_scm to your build environment

.. code-block:: text

   [build-system]
   requires = ["setuptools>=69.0.2", "wheel", "build", "setuptools_scm>=8"]
   build-backend = "setuptools.build_meta"

Currently, only supportedbuild-backend is setuptools. On the to-do list
to add support for more backends.

dynamic version
""""""""""""""""

In ``pyproject.toml``

Minimally make "version" *dynamic*. And set the author name and that
archaic address which forwards to a pr0n site ;-)

.. code-block:: text

   [project]
   dynamic = [
       "optional-dependencies",
       "dependencies",
       "version",
   ]
   authors = [  # Contact by mastodon please
       {name = "Dave Faulkmore", email = "faulkmore@protonmail.com"},
   ]

.. code-block:: text

   [tool.setuptools.dynamic]
   version = {attr = "drain_swamp._version.__version__"}

Change ``drain_swamp`` to your package name

setuptools-scm
"""""""""""""""

In ``pyproject.toml``

.. code-block:: text

   [tool.setuptools_scm]
   # can be empty if no extra settings are needed, presence enables setuptools_scm
   # SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="1.0.2" python -m setuptools_scm
   fallback_version = "1.0.2"
   version_file = "src/drain_swamp/_version.py"

Again change ``drain_swamp`` to your package name

In ``setup.py``, create the linkage between ``setuptools-scm`` and ``setuptools``.

.. code-block:: text

   from setuptools import setup
   from setuptools_scm.version import (
       get_local_node_and_date,
       guess_next_dev_version,
   )
   def _clean_version():
       return {
           "local_scheme": get_local_node_and_date,
           "version_scheme": guess_next_dev_version,
       }

   setup(
       use_scm_version=_clean_version,
   )

Figuring out how this ^^ code works is an ugly rabbit hole. Like dog
shiat, best not to step in it. Copy+paste into ``setup.py`` then brush teeth,
gargle, and try to forget. Don't thank me, just forget it ever happened.

Provide defaults
"""""""""""""""""

This is on the todo list. Currently have to provide options on the command line

.. code-block:: text

   [tool.sphinxcontrib-snip]
   copyright_start_year = 2024  # this is an int, not a str
   snippet_co = "vampire_smoothie_machines"

``--kind`` is either "tag", "current" or "now", or a version str.

Will normally be creating tagged releases. In which case, always on the
command line provide a version str.

Default is "current" for development releases.

"tag" is last tagged release. If there is no tagged releases, fallback to "current".

:command:`sphinxcontrib-snip` has the **side effect** of updating
``src/[package_name]/_version.py``.

Keep a laser eye on that file!

If it's not what you want, change it.

For example, when making tagged (, pre, post, and rc) releases. It's changed by hand.
