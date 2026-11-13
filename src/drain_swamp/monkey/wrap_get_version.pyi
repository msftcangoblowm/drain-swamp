import logging
from collections.abc import Callable
from typing import (
    Any,
    Final,
)

try:
    # setuptools_scm>=8,<10
    import setuptools_scm._types as _t
    from setuptools_scm import (
        Configuration,
        ScmVersion,
    )
except (ImportError, ModuleNotFoundError):
    # setuptools_scm>=10
    import vcs_versioning._types as _t
    from vcs_versioning import ScmVersion
    from vcs_versioning._config import Configuration

log: logging.Logger

__all__ = (
    "scm_version",
    "write_to_file",
    "SEM_VERSION_FALLBACK_SANE",
)

SEM_VERSION_FALLBACK_SANE: Final[str]

try_parse: list[Callable[[_t.PathT, Configuration], ScmVersion | None]]

# setuptools-scm>10 with vcs_versioning
def _scm_version_format(scm_version: ScmVersion) -> str | None: ...

# setuptools-scm>=8,<10
def _parse(root: str, config: Configuration) -> ScmVersion | None: ...

# both
def scm_version(
    relative_to: str,
    sane_default: Any | None = ...,
    tool_names: list[str] = ...,
) -> str: ...
def write_to_file(
    name: str,
    str_ver: str,
    write_to: str | None = None,
    dist_name: str | None = None,
    is_only_not_exists: bool | None = False,
) -> None: ...
