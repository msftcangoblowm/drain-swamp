drain-swamp
============

.. py:module:: drain_swamp.cli_igor
   :platform: Unix
   :synopsis: Update changelog, NOTICE.txt and ``docs?/conf.py``

   Entrypoint which updates: changelog, NOTICE.txt and ``docs?/conf.py``

   .. py:data:: _logger
      :type: logging.Logger

      Module level logger

   .. py:data:: entrypoint_name
      :type: str
      :value: "drain-swamp"

      Command line entrypoint file name

   .. py:data:: help_path
      :type: str

      cli option ``--path`` doc string

   .. py:data:: help_kind
      :type: str

      cli option ``--kind`` doc string

   .. py:data:: help_snippet_co
      :type: str

      cli option --snip doc string

   .. py:data:: EPILOG_SEED
      :type: str

      Exit codes explanation for command, ``seed``

   .. py:data:: EPILOG_EDITS
      :type: str

      Exit codes explanation for command, ``edits``

   .. py:data:: EPILOG_LIST
      :type: str

      Exit codes explanation for command, ``list``

   .. py:data:: EPILOG_BUILD
      :type: str

      Exit codes explanation for command, ``build``

   .. py:data:: EPILOG_SCM_PAIR
      :type: str

      Exit codes explanation for command, ``write_version``

   .. py:data:: EPILOG_PRETAG
      :type: str

      Exit codes explanation for command, ``pretag``

   .. py:data:: EPILOG_CURRENT_VERSION
      :type: str

      Exit codes explanation for command, ``current``

   .. py:data:: EPILOG_TAG_VERSION
      :type: str

      Exit codes explanation for command, ``tag``

   .. py:data:: EPILOG_CHEATS
      :type: str

      Exit codes explanation for command, ``cheats``

   .. py:function:: main()

      :command:`drain-swamp --help`, prints help

      :command:`drain-swamp COMMAND --help`, prints help for a command

      .. csv-table:: Commands
         :header: command, desc, status
         :widths: auto

         :py:func:`seed <drain_swamp.cli_igor.seed>`, "Updates changelog, CHANGES.rst, creating placeholder", ""
         :py:func:`edit <drain_swamp.cli_igor.edit>`, "doc?/conf.py, NOTICE.txt, and CHANGES.rst", ""
         :py:func:`list <drain_swamp.cli_igor.snippets_list>`, "list snippets in doc?/conf.py", ""
         :py:func:`pretag <drain_swamp.cli_igor.validate_tag>`, "Print the sanitized semantic version str", ""
         :py:func:`current <drain_swamp.cli_igor.current_version>`, "Get scm version str", ""
         :py:func:`tag <drain_swamp.cli_igor.tag_version>`, "Get version str from version file", ""
         :py:func:`cheats <drain_swamp.cli_igor.do_cheats>`, "Get useful notes to aid in kitting and publishing", ""
         :py:func:`build <drain_swamp.cli_igor.semantic_version_aware_build>`, "Build package", "depreciated"
         :py:func:`write_version <drain_swamp.cli_igor.setuptools_scm_key_value_pair>`, "Given kind, write version str to version_file", "depreciated"

   .. autofunction:: drain_swamp.cli_igor.seed

   .. autofunction:: drain_swamp.cli_igor.edit

   .. autofunction:: drain_swamp.cli_igor.snippets_list

   .. autofunction:: drain_swamp.cli_igor.validate_tag

   .. autofunction:: drain_swamp.cli_igor.current_version

   .. autofunction:: drain_swamp.cli_igor.tag_version

   .. autofunction:: drain_swamp.cli_igor.do_cheats

   .. autofunction:: drain_swamp.cli_igor.semantic_version_aware_build

   .. autofunction:: drain_swamp.cli_igor.setuptools_scm_key_value_pair
