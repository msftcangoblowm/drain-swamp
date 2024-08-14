import logging
from collections.abc import Mapping
from pathlib import Path
from typing import (
    Any,
    Final,
)

from drain_swamp.monkey.hooks import markers

log: Final[logging.Logger]

def _is_set_lock(
    config_settings: Mapping[str, Any],
    default: Any | None = False,
) -> bool | None: ...
def _parent_dir(
    config_settings: Mapping[str, Any],
    default: Any | None = None,
) -> Path | None: ...
def _snippet_co(
    config_settings: Mapping[str, Any],
    default: Any | None = None,
) -> str | None: ...
@markers.hook_impl(tryfirst=True, specname="ds_before_version_infer")  # noqa: Y020
def before_version_infer(config_settings: Mapping[str, Any]) -> str | None: ...
