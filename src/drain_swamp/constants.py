"""
.. moduleauthor:: |author-contact|

package level constants

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str, str, str, str]
   :value: ("g_app_name", "package_name", "SUFFIX_IN", "SUFFIX_SHARED_IN", \
   "SUFFIX_LOCKED", "SUFFIX_UNLOCKED", "SUFFIX_SYMLINK", "PATH_PIP_COMPILE", \
   "PROG_LOCK", "PROG_UNLOCK")

   Module exports

.. py:data:: g_app_name
   :type: str
   :value: "drain_swamp"

   package name. **Not** project name

.. py:data:: package_name
   :type: str
   :value: "drain-swamp"

   g_app_name --> package_name by replacing underscore with hyphen

.. py:data:: SUFFIX_IN
   :type: str
   :value: ".in"

   Uncompiled requirements file suffix

.. py:data:: SUFFIX_SHARED_IN
   :type: str
   :value: ".shared.in"

   uncompiled requirements file suffix. Shared between venvs

.. py:data:: SUFFIX_LOCKED
   :type: str
   :value: ".lock"

   Allowed locked file, file suffix

.. py:data:: SUFFIX_UNLOCKED
   :type: str
   :value: ".unlock"

   Dependency requirements source files, file suffix. Same as used by pip-lock.

   requirements ``in`` files do not set dependency version restrictions
   unless absolutely unavoidable. In which case, every restriction **must**
   be throughly documented to defend the justification for imposing
   such a restriction so know later whether to keep it or not

.. py:data:: SUFFIX_SYMLINK
   :type: str
   :value: ".lnk"

.. py:data:: PATH_PIP_COMPILE
   :type: pathlib.Path

   Absolute path to pip-compile within venv

.. py:data:: PROG_LOCK
   :type: re.Pattern

   Regex compiled Pattern to find [file name].lock files

.. py:data:: PROG_UNLOCK
   :type: re.Pattern

   Regex compiled Pattern to find [file name].in files

"""

import re
import sys
from pathlib import Path

__all__ = (
    "g_app_name",
    "package_name",
    "SUFFIX_IN",
    "SUFFIX_SHARED_IN",
    "SUFFIX_LOCKED",
    "SUFFIX_UNLOCKED",
    "SUFFIX_SYMLINK",
    "PATH_PIP_COMPILE",
    "PROG_LOCK",
    "PROG_UNLOCK",
)

__package__ = "drain_swamp"
g_app_name = "drain_swamp"
# package_name = re.sub(r"\W+", "-", g_app_name.lower())
package_name = g_app_name.lower().replace("_", "-")
SUFFIX_IN = ".in"
SUFFIX_SHARED_IN = ".shared.in"
SUFFIX_LOCKED = ".lock"
SUFFIX_UNLOCKED = ".unlock"
SUFFIX_SYMLINK = ".lnk"

_PATH_VENV = Path(sys.exec_prefix) / "bin"
PATH_PIP_COMPILE = _PATH_VENV / "pip-compile"

# `regex word+hyphens <https://stackoverflow.com/a/8383339>`_
_pattern_lock = r"\w+(?:-\w+{})+".format(SUFFIX_LOCKED)
_pattern_unlock = r"\w+(?:-\w+{})+".format(SUFFIX_UNLOCKED)
PROG_LOCK = re.compile(_pattern_lock)
PROG_UNLOCK = re.compile(_pattern_unlock)
