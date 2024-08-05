"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

package level constants

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str, str, str]
   :value: ("g_app_name", "package_name", "SUFFIX_IN", "SUFFIX_LOCKED", \
   "SUFFIX_UNLOCKED", "SUFFIX_SYMLINK", "PATH_PIP_COMPILE", "PROG_LOCK", \
   "PROG_UNLOCK")

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

.. py:data:: LOGGING
   :type: dict[str, typing.Any]

   logging dict input to logging.dictConfig

   pytest aware. :code:`"propagate": True,` is required by pytest.
   Otherwise cannot see log messages

   If :code:`DEBUG is True` would require package colorlog. So DEBUG
   is purposefully FALSE

   This logging dict formatter requires package, colorlog. colorized
   debug messages is a feature

   The below code was removed

   .. code-block:: text

      'verbose_with_color': {
          '()': 'colorlog.ColoredFormatter',
          'format': '{log_color}{levelname}{reset} {asctime} {cyan}{name}{reset}: {message}',
          'style': '{',
      },

   .. caution::

      This is example of py38- usage. From py39+, this is no longer valid

      .. code-block:: text

         'root': {
              'handlers': ['console'],
              'level': 'INFO',
         },

   .. seealso::

      `pytest#3697 <https://github.com/pytest-dev/pytest/issues/3697#issuecomment-1984895577>`_

      `pytest#10606 <https://github.com/pytest-dev/pytest/issues/10606#issuecomment-1550123106>`_

"""

import re
import sys
from pathlib import Path

__all__ = (
    "g_app_name",
    "package_name",
    "SUFFIX_IN",
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
SUFFIX_LOCKED = ".lock"
SUFFIX_UNLOCKED = ".unlock"
SUFFIX_SYMLINK = ".lnk"

# Required only for pytest
DEBUG = False
IS_TESTING = "pytest" in sys.modules
formatting = "verbose_with_color" if DEBUG else "simple"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": formatting,
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django.server": {  # Suppress django HTTP logging because we do it in a middleware
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": IS_TESTING,
        },
        g_app_name: {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": IS_TESTING,
        },
    },
}

_PATH_VENV = Path(sys.exec_prefix) / "bin"
PATH_PIP_COMPILE = _PATH_VENV / "pip-compile"

# `regex word+hyphens <https://stackoverflow.com/a/8383339>`_
_pattern_lock = r"\w+(?:-\w+{})+".format(SUFFIX_LOCKED)
_pattern_unlock = r"\w+(?:-\w+{})+".format(SUFFIX_UNLOCKED)
PROG_LOCK = re.compile(_pattern_lock)
PROG_UNLOCK = re.compile(_pattern_unlock)
