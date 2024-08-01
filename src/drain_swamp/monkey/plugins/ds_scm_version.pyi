import logging
from typing import Any

from drain_swamp.monkey.hooks import markers

logger: logging.Logger

def is_package_installed(app_name: str) -> bool: ...
def _kind(
    config_settings: dict[str, Any] | None, fallback: str | None = "tag"
) -> str: ...
@markers.hook_impl(specname="ds_before_version_infer")
def on_version_infer(config_settings: dict[str, Any]) -> str | None: ...
