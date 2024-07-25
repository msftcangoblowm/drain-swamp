import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from drain_swamp.monkey.hooks import markers
from drain_swamp.monkey.hooks.constants import HOOK_NAMESPACE

__all__ = ("BuildPackageSCMVersion",)
logger: logging.Logger

def is_package_installed(app_name: str) -> bool: ...
def _kind(
    config_settings: dict[str, Any] | None, fallback: str | None = "tag"
) -> str: ...
@markers.hook_impl(specname=f"{HOOK_NAMESPACE}_on_version_infer")
def on_version_infer(config_settings: dict[str, Any]) -> str | None: ...
