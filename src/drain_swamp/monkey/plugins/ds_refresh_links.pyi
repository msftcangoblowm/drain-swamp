import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from drain_swamp.monkey.hooks import markers
from drain_swamp.monkey.hooks.constants import HOOK_NAMESPACE

from ..hooks.markers import hook_impl

def _is_set_lock(
    config_settings: Mapping[str, Any],
    default: Any | None = False,
) -> bool | None: ...
@markers.hook_impl(tryfirst=True, specname=f"{HOOK_NAMESPACE}_before_version_infer")
def before_version_infer(config_settings: Mapping[str, Any]) -> str | None: ...
