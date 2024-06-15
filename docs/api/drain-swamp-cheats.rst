drain-swamp cheats
===================

Prints useful easy to forget github commands

Normal usage
-------------

From package base folder

.. code-block:: shell

   drain-swamp cheats --kind="tag"

Command options
""""""""""""""""

.. csv-table:: :code:`drain-swamp cheats` options
   :header: cli, default, description
   :widths: auto

   "-p/--path", "cwd", "absolute path to package base folder"
   "-k/--kind", "None", "version string kind: now (alias of current), current, tag, or explicit semantic version"
   "-n/--package-name", "None", "If provided avoids asking git what the package name is. Best to avoid that"
