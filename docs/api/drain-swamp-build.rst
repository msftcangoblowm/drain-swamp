Build package
==============

Normal usage
-------------

From package base folder

.. code-block:: shell

   drain-swamp build --kind="0.0.1"

This will update ``src/[package name]/_version.py``

The output is silent. There will be a delay as the package is being built

Command options
""""""""""""""""

.. csv-table:: :code:`drain-swamp build` options
   :header: cli, default, description
   :widths: auto

   "-p/--path", "cwd", "absolute path to package base folder"
   "-k/--kind", "None", "version string kind: now (alias of current), current, tag, or explicit semantic version"
   "-n/--package-name", "None", "If provided avoids asking git what the package name is. Best to avoid that"

.. csv-table:: kind
   :header: cli, description
   :widths: auto

   "tag", "Get the last tagged version"
   "current", "Get the latest version. Most likely a development version"
   "0.0.1", "Get a specific version. This is a semantic version str"

To get latest version, :code:`drain-swamp current`

From source code
------------------

Example builds development version of swamp-drain

.. code-block:: shell

   python src/drain_swamp/cli_igor.py --kind="current"

Example builds tag version of swamp-drain

.. code-block:: shell

   python src/drain_swamp/cli_igor.py --kind="tag"

Best to provide the explicit semantic version
