import re
from typing import Final

__all__ = (
    "g_app_name",
    "package_name",
    "SUFFIX_IN",
    "SUFFIX_SHARED_IN",
    "SUFFIX_LOCKED",
    "SUFFIX_UNLOCKED",
    "SUFFIX_SYMLINK",
    "PROG_LOCK",
    "PROG_UNLOCK",
)

g_app_name: Final[str]
package_name: Final[str]
SUFFIX_IN: Final[str]
SUFFIX_SHARED_IN: Final[str]
SUFFIX_LOCKED: Final[str]
SUFFIX_UNLOCKED: Final[str]
SUFFIX_SYMLINK: Final[str]

_pattern_lock: str
_pattern_unlock: str
PROG_LOCK: re.Pattern[str]
PROG_UNLOCK: re.Pattern[str]
