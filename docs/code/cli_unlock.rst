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

   .. py:data:: help_snippet_co
      :type: str

      cli option ``--snip`` doc string

   .. py:data:: help_set_lock
      :type: str

      cli option ``--set-lock`` doc string

   .. py:data:: EPILOG_LOCK_UNLOCK
      :type: str

      Exit codes explanation for command, ``lock`` and ``unlock``

   .. py:data:: EPILOG_IS_LOCK
      :type: str

      Exit codes explanation for command, ``is_lock``

   .. py:data:: EPILOG_REFRESH
      :type: str

      Exit codes explanation for command, ``refresh``

   .. py:function:: main()

      :command:`pipenv-unlock --help`, prints help

      :command:`pipenv-unlock COMMAND --help`, prints help for a command

      .. csv-table:: Commands
         :header: command, creates, desc
         :widths: auto

         :py:func:`is_lock <drain_swamp.cli_unlock.state_is_lock>`, "", "Check dependencies lock state"
         :py:func:`lock <drain_swamp.cli_unlock.dependencies_lock>`, ".lock", "Create lock dependency file"
         :py:func:`unlock <drain_swamp.cli_unlock.dependencies_unlock>`, ".unlock", "Create unlock dependency file"
         :py:func:`refresh <drain_swamp.cli_unlock.create_links>`, ".lnk", "Create dependency lock state symlinks"

   .. autofunction:: drain_swamp.cli_unlock.state_is_lock

   .. autofunction:: drain_swamp.cli_unlock.dependencies_lock

   .. autofunction:: drain_swamp.cli_unlock.dependencies_unlock

   .. autofunction:: drain_swamp.cli_unlock.create_links
