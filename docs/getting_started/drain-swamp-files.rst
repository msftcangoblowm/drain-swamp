Create these files
===================

For getting started purposes only

Give example files for: NOTICE.txt, CHANGES.rst, and doc?/conf.py snippet

NOTICE.txt
------------

Copyright 2023-2024 Dave Faulkmore.  All rights reserved. Apache2 License

Except where noted otherwise, this software is licensed under the Apache
License, Version 2.0 (the "License"); you may not use this work except in
compliance with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

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
