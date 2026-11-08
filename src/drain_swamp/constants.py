"""
.. moduleauthor:: |author-contact|

.. py:data:: __all__
   :type: tuple[str, ...]
   :value: ("g_app_name", "package_name", "SUFFIX_IN", "SUFFIX_SHARED_IN", \
   "SUFFIX_LOCKED", "SUFFIX_UNLOCKED", "SUFFIX_SYMLINK", "PROG_LOCK", \
   "PROG_UNLOCK")

.. py:data:: SUFFIX_UNLOCKED
   :type: str
   :value: ".unlock"

   Dependency requirements source files, file suffix. Same as used by pip-lock.

   requirements ``in`` files do not set dependency version restrictions
   unless absolutely unavoidable. In which case, every restriction **must**
   be thoroughly documented to defend the justification for imposing
   such a restriction so know later whether to keep it or not

"""

import re

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

__package__ = "drain_swamp"
#: str: package name. underscores, not hyphens
g_app_name = "drain_swamp"

# package_name = re.sub(r"\W+", "-", g_app_name.lower())
#: str: g_app_name --> package_name by replacing underscore with hyphen
package_name = g_app_name.lower().replace("_", "-")

#: str: Uncompiled requirements file suffix
SUFFIX_IN = ".in"
#: str: uncompiled requirements file suffix. Shared between venvs
SUFFIX_SHARED_IN = ".shared.in"
#: str: Allowed locked file, file suffix
SUFFIX_LOCKED = ".lock"
SUFFIX_UNLOCKED = ".unlock"
#: str: build resolve symlinks. Unused feature?
SUFFIX_SYMLINK = ".lnk"

# `regex word+hyphens <https://stackoverflow.com/a/8383339>`_
_pattern_lock = r"\w+(?:-\w+{})+".format(SUFFIX_LOCKED)
_pattern_unlock = r"\w+(?:-\w+{})+".format(SUFFIX_UNLOCKED)
#: re.Pattern: Regex compiled Pattern to find [file name].lock files
PROG_LOCK = re.compile(_pattern_lock)
#: re.Pattern: Regex compiled Pattern to find [file name].in files
PROG_UNLOCK = re.compile(_pattern_unlock)
