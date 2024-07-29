drain-swamp seed / edits
=========================

Creates a proto-entry within ``CHANGES.rst``. Use precedes :code:`drain-swamp edits`

Usage -- normal
----------------

.. code-block:: shell

   drain-swamp seed
   drain-swamp edits --kind="0.5.0"

Always combined with :code:`drain-swamp edits`

CHANGES.rst
""""""""""""

And voila!

(Excerpt)

.. code-block:: text

   .. scriv-start-here

   .. _changes_0-5-0:

   Version 0.5.0 — 2024-06-10
   --------------------------

   - feat(pipenv-unlock): add command is_lock
   - feat(swamp-drain): add command cheats
   - refactor(entrypoints): py313+ importlib to ignore __package__. Use __spec__
   - fix: click.Path(resolve_path=True) resolves relative path --> absolute path
   - test(pep366): run commands directly. Use only source code
   - test(pep366): integration test. Isolated from 1st run unit tests
   - refactor: retire igor.py

Sphinx doc?/conf.py
""""""""""""""""""""

And voila!

(Excerpt)

.. code-block:: text

   # @@@ editable vampire_smoothie_machines
   copyright = "2024–2024, Dave Faulkmore"
   # The short X.Y.Z version.
   version = "0.5.0"
   # The full version, including alpha/beta/rc tags.
   release = "0.5.0"
   # The date of release, in "monthname day, year" format.
   release_date = "June 10, 2024"
   # @@@ end

NOTICE.txt
"""""""""""

And voila!

(Excerpt)

.. code-block:: text

   Copyright 2024-2024 Dave Faulkmore. AGPLv3+ License

Affects copyright start year. Defaults to 1970. Provide value in ``pyproject.toml``

Command options
----------------

.. csv-table:: :code:`drain-swamp seed` options
   :header: cli, default, description
   :widths: auto

   "-p/--path", "cwd", "absolute path to package base folder"

.. csv-table:: :code:`drain-swamp edits` options
   :header: cli, default, description
   :widths: auto

   "-p/--path", "cwd", "absolute path to package base folder"
   "-k/--kind", "None", "version string kind: now (alias of current), current, tag, or explicit semantic version"
   "-s/--snip", "None", "Snippet code, within a file, unique id of an editable region, aka snippet. Only necessary if multiple snippets"
