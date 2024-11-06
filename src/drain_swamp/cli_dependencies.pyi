import logging
from pathlib import Path
from typing import Final

entrypoint_name: Final[str]

is_module_debug: Final[bool]
_logger: logging.Logger

help_path: Final[str]
help_venv_path: Final[str]
help_timeout: Final[str]
help_is_dry_run: Final[str]
help_show_unresolvables: Final[str]
help_show_fixed: Final[str]
help_show_resolvable_shared: Final[str]

EPILOG_LOCK: Final[str]
EPILOG_UNLOCK: Final[str]
EPILOG_REQUIREMENTS_FIX: Final[str]

def main() -> None: ...
def dependencies_lock(
    path: Path,
    venv_relpath: str,
    timeout: int,
) -> None: ...
def dependencies_unlock(
    path: Path,
    venv_relpath: str,
) -> None: ...
def requirements_fix(
    path: Path,
    venv_relpath: str,
    is_dry_run: bool,
    show_unresolvables: bool,
    show_fixed: bool,
    show_resolvable_shared: bool,
) -> None: ...
