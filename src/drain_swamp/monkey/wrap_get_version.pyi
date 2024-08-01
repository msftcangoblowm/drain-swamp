import logging
from collections.abc import Callable
from typing import (
    Any,
    Final,
)

import setuptools_scm._types as _t
from setuptools_scm import (
    Configuration,
    ScmVersion,
)

log: logging.Logger

__all__ = (
    "scm_version",
    "write_to_file",
    "SEM_VERSION_FALLBACK_SANE",
)

SEM_VERSION_FALLBACK_SANE: Final[str]

try_parse: list[Callable[[_t.PathT, Configuration], ScmVersion | None]]

def _parse(root: str, config: Configuration) -> ScmVersion | None: ...
def scm_version(relative_to: str, sane_default: Any | None = ...) -> str: ...
def write_to_file(
    name: str,
    str_ver: str,
    write_to: str | None = None,
    dist_name: str | None = None,
) -> None: ...
