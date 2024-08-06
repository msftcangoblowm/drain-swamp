"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

.. py:data:: __all__
   :type: tuple[str, str, str, str]
   :value: ("PyProjectTOMLParseError", "BackendNotSupportedError", \
    "PyProjectTOMLReadError", "MissingRequirementsFoldersFiles")

   Package level exports

.. seealso::

   `pep366 <https://peps.python.org/pep-0366/>`_

   `__package__ usage <https://stackoverflow.com/a/48833828>`_

   `import package <https://stackoverflow.com/a/6655098>`_

   `removal of __package__ <https://github.com/python/cpython/pull/97879>`_

"""

__package__ = __name__

from .constants_maybe import __version_app as __version__  # noqa: F401
from .exceptions import (
    BackendNotSupportedError,
    MissingRequirementsFoldersFiles,
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)

__all__ = (
    "PyProjectTOMLParseError",
    "BackendNotSupportedError",
    "PyProjectTOMLReadError",
    "MissingRequirementsFoldersFiles",
)
