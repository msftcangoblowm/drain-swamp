sphinxcontrib-snip
===================

.. py:module:: drain_swamp.cli_sphinx_conf
   :platform: Unix
   :synopsis: Entrypoint sphinxcontrib-snip

   sphinxcontrib-snip entrypoint

   .. py:data:: _logger
      :type: logging.Logger

      Module level logger

   .. py:data:: help_path
      :type: str

      cli option ``--path`` doc string

   .. py:data:: help_kind
      :type: str

      cli option ``--kind`` doc string

   .. py:data:: help_copyright_year
      :type: str

      cli option ``--start-year`` doc string

   .. py:data:: help_snippet_co
      :type: str

      cli option ``--snip`` doc string

   .. py:data:: EPILOG
      :type: str

      Text block following entrypoint description. Explains meaning of each exit code

   .. py:function:: main()

      Typing command, :command:`sphinxcontrib-snip snip --help`, prints help

   .. autofunction:: drain_swamp.cli_sphinx_conf.sphinx_conf_snip
