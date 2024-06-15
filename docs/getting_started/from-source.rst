From source code
=================

Fully support running from source code

``howto.txt`` has instructions on how to package. The package is not
assumed to be installed. So the drain-swamp and pipenv-unlock can run
direct from source code.

Requires:

- an activated virtual environment

- the dependencies installed

- Went thru getting started

This updates: CHANGES.rst, NOTICE.txt, and ``doc?/conf.py``

.. code-block:: shell

   python src/drain_swamp/cli_igor.py seed
   python src/drain_swamp/cli_igor.py edits --kind="0.0.1" --snip="vampire_smoothie_machines"

.. note::

   The ``tests/`` folder, contains unit tests which contribute to coverage

   The ``integration/`` folder contains unit tests that cover running from
   source code functionality. This is not coverage friendly.
