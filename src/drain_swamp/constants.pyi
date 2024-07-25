import re
from pathlib import Path
from typing import Final

__all__ = (
    "g_app_name",
    "package_name",
    "SUFFIX_IN",
    "SUFFIX_LOCKED",
    "SUFFIX_UNLOCKED",
    "SUFFIX_SYMLINK",
    "__version_app",
    "__url__",
    "PATH_PIP_COMPILE",
    "PROG_LOCK",
    "PROG_UNLOCK",
)

g_app_name: Final[str]
package_name: Final[str]
SUFFIX_IN: Final[str]
SUFFIX_LOCKED: Final[str]
SUFFIX_UNLOCKED: Final[str]
SUFFIX_SYMLINK: Final[str]

__version_app: Final[str]
__url__: Final[str]
_PATH_VENV: Path
PATH_PIP_COMPILE: Path
_pattern_lock: str
_pattern_unlock: str
PROG_LOCK: re.Pattern[str]
PROG_UNLOCK: re.Pattern[str]
