scm-version
============

.. py:module:: drain_swamp.cli_version
   :platform: Unix
   :synopsis: Get and write scm version

   Get and write scm version. Codebase scope limited to setuptool-scm codebase

   .. py:data:: entrypoint_name
      :type: str
      :value: "scm-version"

      Command line entrypoint file name

   .. py:data:: help_path
      :type: str

      cli option ``--path`` doc string

   .. py:data:: help_is_write
      :type: str

      cli option ``--is-write`` doc string

   .. py:data:: help_write_to
      :type: str

      cli option ``--write-to`` doc string

   .. py:data:: EPILOG_SCM_VERSION_GET
      :type: str

      Exit codes explanation for command, ``get``

   .. py:data:: EPILOG_SCM_VERSION_WRITE
      :type: str

      Exit codes explanation for command, ``write``

   .. py:function:: main()

      :command:`scm-version --help`, prints help

      :command:`scm-version COMMAND --help`, prints help for a command

      .. csv-table:: Commands
         :header: command, desc, status
         :widths: auto

         :py:func:`get <drain_swamp.cli_scm_version.get_scm_version>`, "Get scm version str", ""
         :py:func:`write <drain_swamp.cli_scm_version.write_scm_version>`, "Write scm version str to version file", ""

   .. autofunction:: drain_swamp.cli_scm_version.get_scm_version

   .. autofunction:: drain_swamp.cli_scm_version.write_scm_version
