api
====

The commands and respective options

Your howto.txt file informs when to use these commands

.. csv-table:: Semantic version str
   :header: "command", "desc"
   :widths: auto

   "scm-version get", "get version from source code manager"
   "drain-swamp tag", "get version from version file"
   "scm-version write", "write semantic version str to version file"
   "drain-swamp pretag", "Print the sanitized semantic version str"


.. csv-table:: Updating package docs
   :header: "command", "desc"
   :widths: auto

   "drain-swamp seed", "called immediately before drain-swamp edits"
   "drain-swamp edits", "updates doc?/conf.py, NOTICE.txt, and CHANGES.rst"
   "drain-swamp list", "list snippets in doc?/conf.py"


.. csv-table:: dependency locks
   :header: "command", "desc"
   :widths: auto

   "pipenv-unlock is_lock", "0 is locked; 1 is unlocked"
   "pipenv-unlock lock", "same as pip-compile. Creates .lock files"
   "pipenv-unlock unlock", "same as pip-compile. Creates .unlock files"
   "pipenv-unlock refresh", "creates/refreshes package dependency lock .lnk symlinks"


.. csv-table:: misc
   :header: "command", "desc"
   :widths: auto

   "drain-swamp cheats", "Prints helpful notes aids in kitting and publishing"


.. csv-table:: depreciated or avoid
   :header: "command", "desc"
   :widths: auto

   "drain-swamp build", "previous build package command"
   "drain-swamp current", "prior impl of scm-version current"


.. tableofcontents::
