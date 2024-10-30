pipenv-unlock
==============

.. py:module:: drain_swamp.cli_unlock
   :platform: Unix
   :synopsis: Entrypoint pipenv-unlock

   Entrypoint for dependency locks

   .. py:data:: entrypoint_name
      :type: str
      :value: "pipenv-unlock"

      Command line entrypoint file name

   .. py:data:: help_path
      :type: str

      cli option ``--path`` doc string

   .. py:data:: help_required
      :type: str

      cli option ``--required`` doc string

   .. py:data:: help_optional
      :type: str

      cli option ``--optional`` doc string

   .. py:data:: help_additional_folder
      :type: str

      cli option ``--dir`` doc string

   .. py:data:: help_is_dry_run
      :type: str

      cli option ``--dry-run`` doc string

   .. py:data:: help_show_unresolvables
      :type: str

      cli option ``--show-unresolvables`` doc string

   .. py:data:: help_show_fixed
      :type: str

      cli option ``--show-fixed`` doc string

   .. py:data:: help_show_resolvable_shared
      :type: str

      cli option ``--show-resolvable-shared`` doc string

   .. py:data:: EPILOG_LOCK_UNLOCK
      :type: str

      Exit codes explanation for command, ``lock`` and ``unlock``

   .. py:data:: EPILOG_REQUIREMENTS_FIX
      :type: str

      Exit codes explanation for command, ``fix``

   .. py:function:: main()

      :command:`pipenv-unlock --help`, prints help

      :command:`pipenv-unlock COMMAND --help`, prints help for a command

      .. csv-table:: Commands
         :header: command, creates, desc
         :widths: auto

         :py:func:`lock <drain_swamp.cli_unlock.dependencies_lock>`, ".lock", "Create lock dependency file"
         :py:func:`unlock <drain_swamp.cli_unlock.dependencies_unlock>`, ".unlock", "Create unlock dependency file"
         :py:func:`fix <drain_swamp.cli_unlock.requirements_fix>`, "", "In requirements, fixes/reports dependency conflicts"

   .. autofunction:: drain_swamp.cli_unlock.dependencies_lock

   .. autofunction:: drain_swamp.cli_unlock.dependencies_unlock

   .. autofunction:: drain_swamp.cli_unlock.requirements_fix
