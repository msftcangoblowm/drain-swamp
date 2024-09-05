"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

From pyproject.toml, retrieve authors name and email.

Only retrieving the left portion of the authors name. In Japanese, that
would be both last name and first name

.. py:data:: __all__
   :type: tuple[str]
   :value: ("PackageMetadata",)

   Module exports

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: AUTHOR_NAME_FALLBACK
   :type: str
   :value: "Anonymous"

   Fallback when unable to get author name, from either package data or pyproject.toml

"""

import copy
import logging
from email.utils import parseaddr
from functools import cache
from importlib.metadata import (
    PackageNotFoundError,
    metadata,
)

from ._package_installed import is_package_installed
from .check_type import is_ok
from .constants import g_app_name
from .parser_in import TomlParser

_logger = logging.getLogger(f"{g_app_name}.package_metadata")

__package__ = "drain_swamp"
__all__ = ("PackageMetadata",)
AUTHOR_NAME_FALLBACK = "Anonymous"


@cache
def get_author_and_email(app_name):
    """Get author name and email from package metadata.

    :param app_name:

       Contains only underscore, not hyphens. Cuz used by
       :py:func:`functools.cache` as a key. So that key must be unique
       across multiple calls

    :type app_name: str
    :returns: Author name, fallback is "Anonymous" and email fallback is None
    :rtype: tuple[str, str | None]
    """
    try:
        package_meta = metadata(app_name)
    except PackageNotFoundError:
        """Package not installed. Fallback to attempting to get from
        ``pyproject.toml``"""
        msg_exc = (
            f"Package, {app_name}, not installed. Could not get author name "
            "from Python package metadata. Default --> Anonymous"
        )
        _logger.warning(msg_exc)
        author_name = AUTHOR_NAME_FALLBACK
        author_email = None
    else:
        rfc2822_addr = package_meta["Author-email"]
        author_name, author_email = parseaddr(rfc2822_addr)

    return (author_name, author_email)


class PackageMetadata:
    """Access author details from either package metadata or cache.

    .. py:attribute:: __slots__
       :type: tuple[str, str, str]
       :value: ("_app_name", "_full_name", "_email")

    :vartype app_name:

       Key used to get the author details either package metadata or cache

    :ivar: typing.Any
    :vartype path:

       Default None. If the package has yet to be installed, fallback
       to ``pyproject.toml``

    :ivar: path: pathlib.Path | None
    """

    __slots__ = ("_app_name", "_full_name", "_email", "_d_pyproject_toml")

    def __init__(self, app_name, path=None):
        """Class constructor."""
        super().__init__()
        self.app_name = app_name

        if is_package_installed(self.app_name):
            self._full_name, self._email = get_author_and_email(self.app_name)
        else:
            # Looks alot like :py:func:`drain_swamp.pep518_read.find_pyproject_toml`
            tp = TomlParser(path)
            d_pyproject_toml = tp.d_pyproject_toml
            if d_pyproject_toml is None:
                self._full_name = AUTHOR_NAME_FALLBACK
                self._email = None
                return

            self._d_pyproject_toml = copy.deepcopy(d_pyproject_toml)

            authors = d_pyproject_toml.get("project", {}).get("authors", [])
            if isinstance(authors, list) and len(authors) >= 1:
                d_author = authors[0]
                self._full_name = d_author["name"]
                self._email = d_author["email"]
            else:
                msg_exc = (
                    "Package not installed and pyproject.toml project.authors "
                    "does not exist or is invalid"
                )
                _logger.warning(msg_exc)
                self._full_name = AUTHOR_NAME_FALLBACK
                self._email = None

    @property
    def app_name(self):
        """Alphanumeric + underscores. Used as a key.

        :returns: app name
        :rtype: str
        """
        return self._app_name

    @app_name.setter
    def app_name(self, val):
        """Setter for app name. Which is the key used to get the author
        details from cache.

        :param val: Either package name (with hyphens) or app name (with underscores)
        :type val: typing.Any
        """
        if is_ok(val):
            self._app_name = val.replace("-", "_")
        else:
            msg_exc = f"Expecting non-empty str got type {type(val)}"
            raise ValueError(msg_exc)

    @property
    def full_name(self):
        """Author name from package metadata. So need to supply in ``pyproject.toml``.

        For example,

        .. code-block:: text

           [project]
           authors = [  # Contact by mastodon please
               {name = "Dave Faulkmore", email = "faulkmore@protonmail.com"},
           ]

        :returns: full author name
        :rtype: str
        """
        return self._full_name

    @property
    def left_name(self):
        """Why not first name? Well in Japanese, name is written last
        then first name. In which case return last name.

        Intended to be used with a regex to parse a Copyright line

        .. code-block:: text

           regex_pattern = r"Copyright {0}.*? {1}".format(
               copyright_start_year,
               author_first_name,
           )

        :returns: Left name which is usually first name, except for Japanese names.
        :rtype: str

        """
        name = self._full_name
        names = name.split()
        ret = names[0]
        return ret

    @property
    def email(self):
        """Author email address as found in package metadata.

        :returns:

           Author email address. To force author to comply and learn
           what's an abacus. Probably useless for contacting the author

           Companies send rejection emails exactly one to two days after
           applying. Automated cron job. The companies are brand
           marketing; there is no job, recruiter, or HR manager. Just
           an unimaginative cron job

        :rtype: str | None
        """
        return self._email

    @property
    def d_pyproject_toml(self):
        """So don't have to get ``pyproject.toml`` repeatedly.

        :returns: pyproject.toml as a dict otherwise None
        :rtype: dict[str, typing.Any] | None
        """
        return self._d_pyproject_toml
