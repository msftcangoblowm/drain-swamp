from collections.abc import Mapping
from typing import Any

from drain_swamp.monkey.hooks import markers

def _is_set_lock(
    config_settings: Mapping[str, Any],
    default: Any | None = False,
) -> bool | None: ...
@markers.hook_impl(tryfirst=True, specname="ds_before_version_infer")  # noqa: Y020
def before_version_infer(config_settings: Mapping[str, Any]) -> str | None: ...
