"""Provides markers for declaring hook specs and implementations

.. py:data:: HOOK_NAMESPACE
   :type: str
   :value: "drain_swamp"

.. py:data:: hook_spec
   :type: pluggy.HookspecMarker

   Hook spec marker variable

.. py:data:: hook_impl
   :type: pluggy.HookimplMarker

   Hook implementation marker variable

.. seealso::

   `pluggy docs <https://pluggy.readthedocs.io/en/stable/#marking-hooks>`_
   `SOURCE <https://raw.githubusercontent.com/kedro-org/kedro/main/kedro/framework/hooks/markers.py>`_
   `LICENSE:Apache 2.0 <https://github.com/kedro-org/kedro/blob/main/LICENSE.md>`_

"""

import pluggy

from .constants import HOOK_NAMESPACE

# hook_spec = pluggy.HookspecMarker(HOOK_NAMESPACE)
hook_impl = pluggy.HookimplMarker(HOOK_NAMESPACE)
