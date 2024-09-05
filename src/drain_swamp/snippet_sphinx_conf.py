"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Snip plugin for Sphinx ``conf.py``. Replaces snippet containing variables:

- copyright

- version

- release

- release_date

.. py:data:: __all__
   :type: tuple[str]
   :value: ("SnipSphinxConf", "entrypoint_name")

   Module exports

.. py:data:: entrypoint_name
   :type: str
   :value: "drain-swamp"

   Will use this entrypoint. In ``pyproject.toml``, ``[tool.drain-swamp]``

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

from __future__ import annotations

import datetime
import logging
import textwrap

from .constants import g_app_name
from .package_metadata import PackageMetadata
from .snip import (
    ReplaceResult,
    Snip,
)
from .version_semantic import (
    SemVersion,
    _path_or_cwd,
)

__all__ = ("SnipSphinxConf", "entrypoint_name")

entrypoint_name = "drain-swamp"

_logger = logging.getLogger(f"{g_app_name}.snippet_sphinx_conf")


class SnipSphinxConf:
    """Snip plugin for Sphinx conf.py snippet which sets:

    - copyright
    - version
    - release
    - release_date

    This is done for every tagged release

    Sphinx docs folder name is either ``doc`` or ``docs``. If it's something
    else, complain!

    .. py:attribute:: DOC_FOLDERS
       :type: tuple[str, str]
       :value: ("doc", "docs")

       Possible Sphinx doc folder basename

    :ivar path:

       Default None. absolute path to package base folder. If None, use
       current working folder

    :vartype path: pathlib.Path | None
    :raises:

       - :py:exc:`NotADirectoryError` -- From package base folder there
         is no doc/ or docs/ folder

       - :py:exc:`FileNotFoundError` -- In a doc folder, Sphinx config
         conf.py file not found

    """

    DOC_FOLDERS = ("doc", "docs")

    def __init__(self, path=None):
        """Class constructor."""
        super().__init__()

        # package base folder
        self.path_cwd = path

        # Sphinx conf python file
        self.path_abs_init()

        self._contents = None
        self._sv = None
        self._author_name_left = None

    @classmethod
    def now(cls):
        """Current datetime.

        :returns: current datetime
        :rtype: datetime.datetime
        """
        return datetime.datetime.now()

    @classmethod
    def now_to_str(cls, strftime_str):
        """Format datetime now.

        :param strftime_str: format str
        :type strftime_str: str
        :returns: datetime formatted with strftime format
        :rtype: str
        """
        dt_now = cls.now()
        try:
            ret = dt_now.strftime(strftime_str)
        except (ValueError, TypeError):
            raise

        return ret

    @property
    def path_abs(self):
        """Absolute path to ``doc/conf.py`` or ``docs/conf.py``.

        :returns: package base folder
        :rtype: pathlib.Path
        """
        return self._path_abs

    def path_abs_init(self):
        """Using from package base path or cwd, find doc/ or docs/ folder absolute path.

        :raises:

           - :py:exc:`NotADirectoryError` -- From package base folder
             there is no doc/ or docs/ folder

           - :py:exc:`FileNotFoundError` -- In a doc folder, Sphinx config
             conf.py file not found

        """
        cls = type(self)
        path_abs = None
        for path_child in self.path_cwd.iterdir():
            if path_child.is_dir() and path_child.name in cls.DOC_FOLDERS:
                path_abs = path_child
            else:  # pragma: no cover
                pass

        if path_abs is None:
            msg_exc = "There is no Sphinx docs or doc folder. Choose one and mkdir"
            raise NotADirectoryError(msg_exc)

        path_conf_py = path_abs.joinpath("conf.py")
        if not path_conf_py.exists() or (
            path_conf_py.exists() and not path_conf_py.is_file()
        ):
            msg_exc = "In a doc folder, Sphinx config conf.py file not found"
            raise FileNotFoundError(msg_exc)

        self._path_abs = path_conf_py

    @property
    def path_cwd(self):
        """Get package base folder.

        :returns: package base folder
        :rtype: pathlib.Path
        """
        return self._path_cwd

    @path_cwd.setter
    def path_cwd(self, val):
        """Setter of current working directory.

        :param val:

           None will get the current working directory. If not None,
           pass in a temp folder

        :type val: typing.Any | None
        """
        self._path_cwd = _path_or_cwd(val)

    @property
    def SV(self) -> SemVersion | None:
        """Getter for SemVersion instance.

        :returns: After call to contents, SemVersion instance is available
        :rtype: SemVersion | None
        """
        return self._sv

    @property
    def author_name_left(self) -> str | None:
        """Getter for author name, but just the left portion.

        In Japanese, this is the full name. Otherwise would be the first name

        Used within regex to replace copyright notice

        :returns: Author name left. If contents yet to be called will be None
        :rtype: str | None
        """
        return self._author_name_left

    def contents(
        self,
        kind,
        package_name,
        copyright_start_year,
    ):
        """Create the snippet for Sphinx ``conf.py``.

        This will set:

        - copyright
        - version
        - release
        - release_date

        This is done for every tagged release

        Sphinx docs folder name is either ``doc`` or ``docs``. If it's something
        else, complain!

        :param kind:

           Explicit version str or "current"|"now" or "tag". ``tag`` for
           the latest tagged version. Current for the latest version
           which is probably the development version

        :type kind: str
        :param package_name:

           Can contain either hyphen or underscore. Both will work. From
           the package name can get the author name and email address. Only
           interested in the author name

        :type package_name: str
        :param copyright_start_year: This packages copyright start year
        :type copyright_start_year: str
        :raises:

           - :py:exc:`AssertionError` -- Expected Sphinx docs folder to be
             either ``doc/`` or ``docs/``

           - :py:exc:`ValueError` -- Explicit version str is invalid

        """
        cls = type(self)
        sv = SemVersion(path=self.path_cwd)
        path_project_base_dir = sv.path_cwd
        try:
            # Supply package name
            ver_full = sv.version_clean(kind)
        except (AssertionError, ValueError):
            self._contents = None
            raise

        # For use outside of the scope of Sphinx conf.py
        self._sv = sv

        """get authors name from package metadata then pyproject.toml
        Fallback --> "Anonymous"
        """
        author = PackageMetadata(package_name, path=path_project_base_dir)
        # For use outside of the scope of Sphinx conf.py
        self._author_name_left = author.left_name

        self._sv.parse_ver(ver_full)
        ver_xyz = self._sv.version_xyz()

        # \N{EN DASH} is a unicode char, elongated hyphen
        now_year = cls.now_to_str("%Y")
        # replaces f"""{self.now:%B %-d, %Y}"""
        now_full = cls.now_to_str("%B %-d, %Y")
        contents = textwrap.dedent(
            f"""\
            copyright = "{copyright_start_year}\N{EN DASH}{now_year}, {author.full_name}"
            # The short X.Y.Z version.
            version = "{ver_xyz}"
            # The full version, including alpha/beta/rc tags.
            release = "{ver_full}"
            # The date of release, in "monthname day, year" format.
            release_date = "{now_full}"
            """
        )
        self._contents = contents.rstrip()

    def replace(self, snippet_co=None):
        """In a Sphinx conf.py file, for a given snippet, replace contents.

        :param snippet_co:

           Default None. id of snippet within Sphinx ``conf.py``. If
           None, that snippet better not have an id or there be other
           snippets in that file

        :type snippet_co: str | None
        :returns:

           - VALIDATE_FAIL -- Invalid snippet
           - NOMATCH -- no matching snippet with snippet_co
           - NO_CHANGE -- no replacement occurred
           - REPLACED -- replaced contents

        :rtype: drain_swamp.snip.ReplaceResult
        """
        # is_ok check avoids, TypeError
        contents = self._contents
        if contents is not None:
            snip = Snip(self.path_abs, is_quiet=True)
            ret = snip.replace(contents, id_=snippet_co)
        else:  # pragma: no cover
            ret = ReplaceResult.NO_CHANGE

        return ret
