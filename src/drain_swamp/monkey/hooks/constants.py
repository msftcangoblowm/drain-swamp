"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Keep constants out of package module, ``__init__.py``

.. py:data:: __all__
   :type: tuple[str, str, str]
   :value: ("_PLUGIN_HOOKS", "DOTTED_PATH_SPECS", "HOOK_NAMESPACE")

   Module exports

.. py:data:: _PLUGIN_HOOKS
   :type: str
   :value: "ds.hooks"

   Entrypoint name, not the dotted path:fcn. Entrypoint underwhich to specify additional hooks

.. py:data:: DOTTED_PATH_SPECS
   :type: str
   :value: "drain_swamp.monkey.hooks.specs"

   Dotted path to pluggy plugin specs

.. py:data:: HOOK_NAMESPACE
   :type: str
   :value: "ds"

   .. seealso::

      namespace
      `naming conversion <https://pluggy.readthedocs.io/en/latest/#a-complete-example>`_


"""

__all__ = (
    "_PLUGIN_HOOKS",
    "DOTTED_PATH_SPECS",
    "HOOK_NAMESPACE",
)

_PLUGIN_HOOKS = "ds.hooks"
DOTTED_PATH_SPECS = "drain_swamp.monkey.hooks.specs"
HOOK_NAMESPACE = "ds"
