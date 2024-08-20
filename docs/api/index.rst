api
====

The commands and respective options

Your howto.txt file informs when to use these commands

.. card:: version
   :text-align: left
   :shadow: none

   .. csv-table::
      :header: "command", "desc"
      :widths: auto

      "scm-version get", "| get scm version
      | 0.0.1post0.dev4+g123456-d20241212"
      "drain-swamp tag", "| get version from version file
      | 0.0.1post0"
      "scm-version write", "write semantic version str to version file"
      :doc:`drain-swamp pretag <drain-swamp-pretag>`, "Print/fix a semantic version str"

   +++
   :doc:`Version file </code/general/version_file>`

.. raw:: html

   <div class="white-space-5px"></div>

.. card:: Update package docs
   :text-align: left
   :shadow: none

   .. csv-table::
      :header: "command", "desc"
      :widths: auto

      :doc:`drain-swamp seed <drain-swamp-seed>`, "called immediately before drain-swamp edits"
      :doc:`drain-swamp edits <drain-swamp-seed>`, "updates doc?/conf.py, NOTICE.txt, and CHANGES.rst"
      :doc:`drain-swamp list <drain-swamp-list>`, "list snippets in doc?/conf.py"

   +++
   :ref:`Updating changelog <code/cli_igor:main>`

.. raw:: html

   <div class="white-space-5px"></div>

.. card:: Dependency locks
   :text-align: left
   :shadow: none

   .. csv-table::
      :header: "command", "desc"
      :widths: auto

      :doc:`pipenv-unlock is_lock <pipenv-unlock-is_lock>`, "| 0 is locked
      | 1 is unlocked"
      :doc:`pipenv-unlock lock <pipenv-unlock-lock>`, "same as pip-compile. Creates .lock files"
      :doc:`pipenv-unlock unlock <pipenv-unlock-unlock>`, "recursively assembles .in --> .unlock files"
      "pipenv-unlock refresh", "| creates/refreshes package dependency lock .lnk symlinks
      | updates pyproject.toml dependencys' suffix"

   +++
   :ref:`Dependencies <getting_started/pipenv-unlock:dependencies>`

.. raw:: html

   <div class="white-space-5px"></div>

.. card:: Misc
   :text-align: left
   :shadow: none

   .. csv-table::
      :header: "command", "desc"
      :widths: auto

      :doc:`drain-swamp cheats <drain-swamp-cheats>`, "Prints helpful notes aids in kitting and publishing"

.. raw:: html

   <div class="white-space-5px"></div>

.. card:: Deprecated / outdated
   :text-align: left
   :shadow: none

   .. csv-table::
      :header: "command", "desc"
      :widths: auto

      :doc:`drain-swamp build <drain-swamp-build>`, "previous build package command"
      :doc:`drain-swamp current <drain-swamp-current>`, "prior impl of scm-version current"
