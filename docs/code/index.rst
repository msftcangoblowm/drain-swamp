Code manual
============

.. Apache 2.0 https://github.com/google/material-design-icons
.. Browse Google Material Symbol icons https://fonts.google.com/icons
.. colors https://sphinx-design.readthedocs.io/en/latest/css_classes.html#colors

.. grid:: 2
   :margin: 3
   :padding: 2
   :gutter: 3 3 3 3

   .. grid-item-card:: :material-twotone:`login;2em;sd-text-success` Entrypoints
      :class-card: sd-border-0

      - :doc:`cli_unlock`
      - :doc:`cli_igor`
      - :doc:`cli_scm_version`

   .. grid-item-card:: :material-twotone:`pinch;2em;sd-text-primary` Snippet
      :class-card: sd-border-0
      :link-type: url
      :link: https://drain-swamp-snippet.readthedocs.io/en/stable/code/snip.html#drain_swamp_snippet.snip.Snip
      :link-alt: Snippet base package drain-swamp-snippet has class Snip and enum ReplaceResult

      - drain_swamp_snippet.Snip
      - drain_swamp_snippet.ReplaceResult

   .. grid-item-card:: :material-twotone:`lock_open;2em;sd-text-success` Dependency locking
      :class-card: sd-border-0

      - :doc:`backend abc <ext/pipenv_unlock/backend_abc>`
      - :doc:`snippet dependencies <ext/pipenv_unlock/snippet_dependencies>`
      - :doc:`lock toggle <ext/pipenv_unlock/lock_toggle>`
      - :doc:`snippet pyproject.toml <ext/pipenv_unlock/snippet_pyproject_toml>`

   .. grid-item-card:: :material-twotone:`extension;2em;sd-text-success` drain-swamp utils
      :class-card: sd-border-0

      - :doc:`version semantic <general/version_semantic>`
      - :doc:`Sphinx conf <ext/drain_swamp/sphinx_conf>`
      - :doc:`Igor.py utils <ext/drain_swamp/igor_utils>`

   .. grid-item-card:: :material-twotone:`foundation;2em;sd-text-muted` Core
      :class-card: sd-border-0

      - :doc:`Constants <general/constants>`
      - :doc:`Version file <general/version_file>`
      - :doc:`Constants maybe <general/constants_maybe>`
      - :doc:`Exceptions <general/exceptions>`
      - :doc:`Check type <general/check_type>`
      - :doc:`pyproject.toml read <general/pep518_read>`
      - :doc:`pyproject.toml parser <general/parser_in>`
      - :doc:`Package metadata <general/package_metadata>`
      - :doc:`Package installed <general/package_installed>`
      - :doc:`Run command <general/run_cmd>`

   .. grid-item-card:: :octicon:`versions;2em;sd-text-success` Version file
      :class-card: sd-border-0

      - :doc:`Overrides <version_file/overrides>`
      - :doc:`Dump <version_file/dump_version>`

drain-swamp has built-in build plugins and is extendable.

.. note:: code isolation

   Lets not reinvent the wheel.

   Care is taken to leverage the upstream codebases. Counter-intuitively,
   there is less reliance on the drain-swamp codebase

.. grid:: 2
   :margin: 3
   :padding: 2
   :gutter: 3 3 3 3

   .. grid-item-card:: :material-twotone:`settings;2em;sd-text-muted` Core
      :class-card: sd-border-0

      - :doc:`monkey/config_settings`
      - :doc:`monkey/patch_pyproject_reading`

   .. grid-item-card:: :material-twotone:`schedule;2em;sd-text-primary` Plugin manager
      :class-card: sd-border-0

      - :doc:`PM subpackage <monkey/hooks/index>`
      - :doc:`PM constants <monkey/hooks/pm_constants>`
      - :doc:`Hook implementation markers <monkey/hooks/markers>`
      - :doc:`Hook specs <monkey/hooks/specs>`
      - :doc:`Plugin Manager <monkey/hooks/manager>`

   .. grid-item-card:: :material-twotone:`extension;2em;sd-text-success` Plugins
      :class-card: sd-border-0

      - :doc:`Plugins subpackage <monkey/plugins/index>`
      - :doc:`Refresh links <monkey/plugins/refresh_links>`
      - :doc:`SCM version <monkey/plugins/scm_version>`

   .. grid-item-card:: :material-twotone:`build;2em;sd-text-success` Build integration
      :class-card: sd-border-0

      - :doc:`Get version <monkey/wrap_get_version>`
      - :doc:`Infer version <monkey/wrap_infer_version>`
      - :doc:`Version keyword <monkey/wrap_version_keyword>`

.. module:: drain_swamp
   :platform: Unix
   :synopsis: package level exports

    .. py:data:: drain_swamp.__all__
       :type: tuple[str, str, str, str]
       :value: ("PyProjectTOMLParseError", "BackendNotSupportedError", "PyProjectTOMLReadError", "MissingRequirementsFoldersFiles")

       Package level exports are limited to just custom exceptions. This was originally
       done to avoid unexpected side effects
