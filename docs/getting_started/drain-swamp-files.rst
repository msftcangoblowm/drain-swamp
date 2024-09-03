Create these files
===================

For getting started purposes only

Give example files for: NOTICE.txt, CHANGES.rst, and doc?/conf.py snippet

NOTICE.txt
------------

.. code-block:: text

   Copyright (C) 2023-2024 Dave Faulkmore

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU Affero General Public License as published
   by the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Affero General Public License for more details.

   You should have received a copy of the GNU Affero General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.

What gets updated?
"""""""""""""""""""

Copyright end year

Copyright start year is specified in ``pyproject.toml``

Sphinx doc?/conf.py
--------------------

Sphinx are either in:

- doc/conf.py

or

- docs/conf.py

Contains block

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

Can start out the block as

Without a snippet_co

.. code-block:: text

   # @@@ editable
   # @@@ end

or with a snippet_co

.. code-block:: text

   # @@@ editable vampire_smoothie_machines
   # @@@ end

And the block will be filled in by these commands

More than one snippet (in Sphinx doc?/conf.py)

.. code-block:: shell

   drain-swamp seed
   drain-swamp edits --kind="0.0.1" --snip="vampire_smoothie_machines"

Only one snippet; snippet_co will be automatically inferred

.. code-block:: shell

   drain-swamp seed
   drain-swamp edits --kind="0.0.1"

CHANGES.rst
-------------

This is skeleton change log

.. code-block:: text

   .. this will be appended to README.rst

   Changelog
   =========

   ..

      Feature request
      .................

      Known regressions
      ..................

      Commit items for NEXT VERSION
      ..............................

   .. scriv-start-here

   .. scriv-end-here
