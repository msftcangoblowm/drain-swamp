import logging
from typing import Any

import setuptools
from pluggy import PluginManager

log: logging.Logger

def inspect_pm(pm: PluginManager) -> None: ...
def run_build_plugins(d_config_settings: dict[str, Any]) -> None: ...
def infer_version(dist: setuptools.Distribution) -> None: ...
