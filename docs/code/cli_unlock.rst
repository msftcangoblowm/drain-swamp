pipenv-unlock
==============

.. py:module:: drain_swamp.cli_unlock
   :platform: Unix
   :synopsis: Entrypoint pipenv-unlock

   pipenv-unlock entrypoint

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

   .. py:data:: EPILOG
      :type: str

      Text block following entrypoint description. Explains meaning of each exit code

   .. py:function:: main()

      :command:`pipenv-unlock --help`, prints help

      :command:`pipenv-unlock unlock --help`, prints unlock command help

      :command:`pipenv-unlock lock --help`, prints lock command help

   .. autofunction:: drain_swamp.cli_unlock.dependencies_lock
   .. autofunction:: drain_swamp.cli_unlock.dependencies_unlock
