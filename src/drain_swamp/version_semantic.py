"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

git --> setuptools-scm --> kitting (howto.txt / igor.py / Makefile) --> semantic versioning

.. seealso::

   packaging.version.Version
   `[docs] <https://packaging.pypa.io/en/stable/version.html>`_

Release phases
---------------

Without SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP environmental variable
locals are included in version

e.g. "0.1.1.dev0+g4b33a80.d20240129" local is "g4b33a80.d20240129"

When releasing this is not what is wanted, so use
SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP with the version

- Current version

  .. code-block:: shell

     PYTHONWARNINGS="ignore" python setup.py --version


- Release by tag aka final

  .. code-block:: shell

     PYTHONWARNINGS="ignore" SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="$(git describe --tag)" python setup.py --version
     SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="$(git describe --tag)" python -m build


- alpha: a, beta: b, or candidate: rc

  .. code-block:: shell

     PYTHONWARNINGS="ignore" SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.1.1a1" python setup.py --version
     SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.1.1a1" python -m build


- dev

  .. code-block:: shell

     PYTHONWARNINGS="ignore" SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.1.1a1.dev1" python setup.py --version
     SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.1.1a1.dev1" python -m build


Move the tag past post commits

- post

  .. code-block:: shell

     PYTHONWARNINGS="ignore" SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.1.1.post1" python setup.py --version
     SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.1.1.post1" python -m build


.. py:data:: __all__
   :type: tuple[str, str, str, str]
   :value: ("SemVersion", "SetuptoolsSCMNoTaggedVersionError", "sanitize_tag", \
   "get_version")

   Module exports

.. py:data:: _map_release
   :type: types.MappingProxyType[str, str]
   :value: types.MappingProxyType({"alpha": "a", "beta": "b", "candidate": "rc"})

   Mapping of release levels. So can gracefully go back and forth

   Read only mapping. key is long name. value is abbreviation. Long
   names will be converted into the abbreviations

"""

import os
import subprocess
import sys
import types
from collections.abc import Sequence
from functools import partial
from pathlib import (
    Path,
    PurePath,
)

try:
    from packaging.version import InvalidVersion
    from packaging.version import Version as Version
except ImportError:  # pragma: no cover
    from setuptools.extern.packaging.version import InvalidVersion  # type: ignore
    from setuptools.extern.packaging.version import Version as Version  # type: ignore

__package__ = "drain_swamp"
__all__ = (
    "SemVersion",
    "SetuptoolsSCMNoTaggedVersionError",
    "sanitize_tag",
    "get_version",
)

_map_release = types.MappingProxyType({"alpha": "a", "beta": "b", "candidate": "rc"})


class SetuptoolsSCMNoTaggedVersionError(AssertionError):
    """Neither a tagged version nor a first commit. Create a commit and
    preferrably a tagged version

    Do not rely on sibling modules, vendor the Exception

    :ivar msg: The error message
    :vartype msg: str
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


def _is_setuptools_scm():
    """Without importing package, check setuptools-scm package is installed

    :returns: True if setuptools-scm package is installed otherwise False
    :rtype: bool
    :meta private:
    """
    from importlib.metadata import (
        PackageNotFoundError,
        version,
    )

    try:
        version("setuptools-scm")
    except PackageNotFoundError:
        bol_ret = False
    else:
        bol_ret = True

    return bol_ret


def _path_or_cwd(val):
    """Frequently used and annoying to test multiple times

    Should be a Path. If anything else return cwd

    :param path: Should be a Path
    :type path: typing.Any | None
    :returns: Path or cwd Path
    :rtype: pathlib.Path
    :meta private:
    """
    if val is None or not issubclass(type(val), PurePath):
        path_cwd = Path.cwd()
    else:
        path_cwd = val

    return path_cwd


def _scm_key(prog_name):
    """When want to set a specific version, setuptools-scm offers an
    environment variable which overrides normal behavior

    This is needed when wanting to create a:
    - tagged version
    - post-release version
    - pre-release version

    :param prog_name:

       package name. Will upper case and replace hyphens with underscores

    :type prog_name: str
    :returns: environment variable to affect setuptools-scm behavior
    :rtype: str
    :meta private:
    """
    # hyphen --> underscore. Uppercase
    G_APP_NAME = prog_name.upper()
    G_APP_NAME.replace("-", "_")
    scm_override_key = f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{G_APP_NAME}"

    return scm_override_key


def _current_tag(path=None):
    """Tagged version as known by git. If there is no tagged version, make one!

    Until a tagged version exists, the version string will not be a
    valid semantic version.

    The git version is authoritative, **not** some hardcoded version str
    in a module within a Python package

    Runs :command:`git describe --tag`

    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :returns:

       None indicates there are no tagged versions otherwise the latest tagged version

    :rtype: str | None
    :meta private:
    """
    path_cwd = _path_or_cwd(path)

    cmd = ["/bin/git", "describe", "--tag"]
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(path_cwd),
            text=True,
        )
    except subprocess.CalledProcessError:
        # git says, no tagged version
        str_out = None
    else:
        # No tags yet
        # 128 -- fatal: No names found, cannot describe anything.
        int_exit_code = proc.returncode
        is_error = int_exit_code != 0
        if not is_error:
            str_out = proc.stdout
            str_out = str_out.rstrip()
        else:
            str_out = None

    return str_out


def _strip_epoch(ver):
    """Strip epoch

    :param ver: May contain epoch, ``v``, and local
    :type ver: str
    :returns: epoch and remaining str including ``v`` and local
    :rtype: tuple[str | None, str]
    :meta private:
    """
    try:
        idx = ver.index("!")
    except ValueError:
        # Contains no epoch
        epoch = None
        remaining = ver
    else:
        epoch = ver[: idx + 1]
        remaining = ver[idx + 1 :]

    return epoch, remaining


def _strip_local(ver):
    """Strip local from end of version string

    From ``0!v1.0.1.a1dev1+g4b33a80.d20240129``

    local: ``g4b33a80.d20240129``

    remaining: ``0!v1.0.1.a1dev1``

    :param ver: full version str from git. May include epoch and local
    :type ver: str
    :returns: local and remaining
    :rtype: tuple[str | None, str]
    :meta private:
    """
    try:
        idx = ver.index("+")
    except ValueError:
        # Contains no local
        local = None
        remaining = ver
    else:
        local = ver[idx + 1 :]
        remaining = ver[:idx]

    return local, remaining


def _remove_v(ver):
    """Remove prepended v. e.g. From ``0!v1.0.1.a1dev1+g4b33a80.d20240129``

    Will not work on an initial untagged version, ``0.1.dev0.d20240213``

    :param ver: Non-initial untagged version
    :type ver: str
    :returns: original str without the v. Includes epoch and local
    :rtype: str
    :meta private:
    """
    epoch, remaining = _strip_epoch(ver)
    local, remaining = _strip_local(remaining)

    # If prepended "v", remove it. epoch e.g. ``1!v1.0.1`` would conceal the "v"
    if remaining.startswith("v"):
        remaining = remaining[1:]

    ret = epoch if epoch is not None else ""
    ret += remaining

    if local is not None:
        ret += f"+{local}"
    else:  # pragma: no cover
        pass

    return ret


def sanitize_tag(ver):
    """Avoid reinventing the wheel, leverage Version

    ``final`` is not valid

    :param ver: raw semantic version
    :type ver: str
    :returns: Sanitized semantic version str
    :rtype: str
    :raises:

       - :py:exc:`ValueError` -- Invalid token within Version str

    """
    # Careful! Will choke on initial untagged version, e.g. ``0.1.dev0.d20240213``
    str_remaining_whole = _remove_v(ver)

    # Strip epoch, if exists
    epoch, str_remaining_stripped = _strip_epoch(str_remaining_whole)

    """Strip local, if exists

    Will fail to detect an initial untagged version e.g. '0.1.dev0.d20240213'"""
    local, str_remaining_stripped = _strip_local(str_remaining_stripped)

    # Problematic
    # '0.1.dev0.d20240213'. Untagged version. Try remove from last period
    # 0.1.1.candidate1dev1+g4b33a80.d20240129
    try:
        v = Version(str_remaining_whole)
    except InvalidVersion:
        is_problem = True
    else:
        is_problem = False

    if is_problem:
        lst = str_remaining_whole.split(".")

        ver_try = ".".join(lst[:-1])
        try:
            v = Version(ver_try)
        except InvalidVersion:
            is_still_issue = True
        else:  # pragma: no cover Do nothing
            is_still_issue = False
    else:  # pragma: no cover Do nothing
        is_still_issue = False

    if is_still_issue:
        try:
            v = Version(str_remaining_whole)
        except InvalidVersion as e:
            msg = f"Version contains invalid token. {e}"
            raise ValueError(msg) from e
    else:  # pragma: no cover Do nothing
        pass

    ret = str(v)

    # Strip epoch and local, if exists
    epoch, ret = _strip_epoch(ret)
    local, ret = _strip_local(ret)

    return ret


def get_version(ver, is_use_final=False):
    """Semantic version string broken into parts

    :param ver: A semantic version string
    :type ver: str
    :param is_use_final:

       Default False. ``final`` is not normally valid within a semantic
       version string. The use of final may be used to indicate intention of creating
       a tagged release version. If all the stars are aligned and its
       G'ds Will. If not, ``post release`` version(s) would occur and
       ``final`` would be incorrect.

       Don't create invalid semantic version strings cuz its convenient.
       Don't use this feature!

    :type is_use_final: bool
    :returns:

       Semantic version broken into parts: major, minor, micro,
       release level, serial. And _dev

    :rtype: tuple[tuple[int, int, int, str, int], int | None]
    :raises:

       - :py:exc:`ValueError` -- Invalid version string. git
         requires one commit. setupttools-scm requires one tagged commit

    """
    if is_use_final is None or not isinstance(is_use_final, bool):
        is_use_final = False
    else:  # pragma: no cover
        pass

    # epoch and locals and prepend v ... remove
    _v = _remove_v(ver)

    try:
        _v = Version(_v)
    except InvalidVersion as e:
        msg = f"Version contains invalid token. {e}"
        raise ValueError(msg) from e

    _dev = _v.dev if _v.is_devrelease else None

    if not _v.is_prerelease and not _v.is_postrelease:
        # ``final`` means intend to bump version. Not actually valid
        releaselevel = "" if not is_use_final else "final"
        serial = 0
        _dev = None
    elif _v.is_prerelease and not _v.is_postrelease:
        # Requires long
        if _v.is_devrelease and _v.pre is None:
            # dev
            serial = 0
            releaselevel = ""  # alpha??
        else:
            # alpha beta, candidate, a, b, or rc
            t_pre = _v.pre
            short = t_pre[0]
            serial = t_pre[1]
            for long_, short_ in _map_release.items():
                if short_ == short:
                    releaselevel = long_
                else:  # pragma: no cover continue
                    pass
    elif not _v.is_prerelease and _v.is_postrelease:
        releaselevel = "post"
        serial = _v.post
    elif _v.is_prerelease and _v.is_postrelease:  # pragma: no cover
        # impossible
        pass
    else:  # pragma: no cover
        pass

    return (_v.major, _v.minor, _v.micro, releaselevel, serial), _dev


def _current_version(path=None):
    """:py:mod:`setuptools_scm` get the current
    version. Which more often than not is a development version

    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :returns:

       Current version as known by setuptools-scm. Avoid returning an empty string

    :rtype: str | None
    :meta private:

    .. note::

       To update ``src/[app name]/_version.py``, use command,
       :code:`python setup.py --version`

    """
    path_cwd = _path_or_cwd(path)

    # Check setuptools-scm package is installed
    if not _is_setuptools_scm():
        return None
    else:  # pragma: no cover
        pass

    # cmd = [sys.executable, "setup.py", "--version"]
    cmd = [sys.executable, "-m", "setuptools_scm"]
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # suppress annoying useless warning
            cwd=str(path_cwd),
            text=True,
        )
    except subprocess.CalledProcessError:  # pragma: no cover
        """setuptools-scm requires at least one commit. Could not get
        semantic version

        Tested using :py:func:`unittest.mock.patch`
        """
        str_out = None
    else:
        str_out = proc.stdout
        str_out = str_out.rstrip()

        # Avoid returning an empty string
        is_cmd_fail = len(str_out) == 0
        if is_cmd_fail:  # pragma: no cover
            """These commands fail with exit code 128. Causes setuptools-scm to also fail

            .. code-block:: shell

               git --git-dir [package home]/.git rev-parse --abbrev-ref HEAD
               git --git-dir [package home]/.git -c log.showSignature=false log -n 1 HEAD --format=%cI

            """
            str_out = None
        else:  # pragma: no cover
            pass

    return str_out


def _tag_version(
    next_version="",
    path=None,
    package_name=None,
):
    """Alias / wrapper for _arbritary_version. Indicating type / purpose
    of the version str.

    :param next_version: Default empty string. If not provided, tagged version
    :type next_version: str | None
    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :param package_name:

       Default None. Package name so as to avoid getting it from git

    :type package_name: str | None
    :returns: tagged version or current version str
    :rtype: str | None
    :meta private:
    :raises:

       - :py:exc:`AssertionError` -- Could not get package name from git

    """
    # empty str means take current tag version
    ret = _arbritary_version(next_version, path=path, package_name=package_name)

    return ret


def _arbritary_version(
    next_version,
    path=None,
    package_name=None,
):
    """Get version **and** setuptools-scm creates the `` _version.py`` file

    :param next_version: Default empty string. If not provided, tagged version
    :type next_version: str
    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :param package_name:

       Default None. Package name so as to avoid getting it from git

    :type package_name: str | None
    :returns: tagged version or current version str. None rather than empty string
    :rtype: str | None
    :meta private:

    :raises:

       - :py:exc:`AssertionError` -- Could not get package name from git

    .. warning::

       This command writes to src/[package name]/_version.py
       Use :py:func:`unittest.mock.patch` to avoid the actual call

    """
    path_cwd = _path_or_cwd(path)
    cwd_path = str(path_cwd)

    # providing the package name is preferred over asking git for it
    is_pkg = (
        package_name is not None
        and isinstance(package_name, str)
        and len(package_name.strip()) != 0
    )
    if is_pkg:
        g_app_name = package_name.replace("-", "_")
    else:
        tmp_name = _get_app_name(path=path_cwd)
        if tmp_name is None:
            msg_exc = "Relies upon git for the package name"
            raise AssertionError(msg_exc)
        else:
            g_app_name = tmp_name

    scm_override_key = _scm_key(g_app_name)

    if next_version is None or (
        next_version is not None
        and isinstance(next_version, str)
        and len(next_version) == 0
    ):
        # If no tags yet will be None
        scm_override_val = _current_tag(path=path_cwd)
    else:
        scm_override_val = next_version

    # Get tagged version number from setup.py
    # https://peps.python.org/pep-0584/
    if scm_override_val is not None:
        env = os.environ.copy()
        env |= {scm_override_key: scm_override_val}
    else:
        # Oh no! Problem. Maybe setuptools-scm will return fallback version
        env = os.environ.copy()

    """env with a tagged version and cmd will change
    ``src/[package name]/_version.py``"""
    cmd = [sys.executable, "setup.py", "--version"]
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # suppress annoying useless warning
            cwd=cwd_path,
            env=env,
            text=True,
        )
    except subprocess.CalledProcessError:  # pragma: no cover
        """setuptools-scm requires at least one commit. Could not get
        semantic version"""
        str_out = None
    else:
        str_out = proc.stdout
        str_out = str_out.rstrip()
        if len(str_out) == 0:
            # setuptools-scm fails to get a version. Reason: Not even one commit
            str_out = None
        else:  # pragma: no cover
            pass

    return str_out


def _get_app_name(path=None):
    """app name contains underscores. Package name contains hyphens.
    Want the app name, not the package name

    Source git. Looks at the local repo, not remote

    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :returns: app name. None if fails to get from git
    :rtype: str | None
    :meta private:

    .. seealso::

       `From git get project name <https://stackoverflow.com/a/33180289>`_

    """
    path_cwd = _path_or_cwd(path)
    cwd_path = str(path_cwd)

    cmd = (
        "/bin/git",
        "rev-parse",
        "--show-toplevel",
    )
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # suppress annoying useless warning
            cwd=cwd_path,
            text=True,
        )
    except subprocess.CalledProcessError:
        ret = None
    else:
        str_out = proc.stdout
        str_out = str_out.rstrip()
        if len(str_out) == 0:
            ret = None
        else:
            str_mixed = Path(str_out).name
            ret = str_mixed.replace("-", "_")

    return ret


class SemVersion:
    """Translates :menuselection:`git version --> Python semantic version`.
    Intended use cases:

    - kitting (building sdist and whl)

    - **not** hardcoding the package str within Python packages

    .. py:attribute:: CURRENT_ALIAS_DEFAULT
       :type: str
       :value: "current"

       Preferred default that is used within code. Indicates to get the
       current git version

    .. py:attribute:: CURRENT_ALIASES
       :type: tuple[str, str]
       :value: ("current", "now")

       Aliases which means current (version)

    .. py:attribute:: KINDS
       :type: tuple[str, str, str]
       :value: ("tag", "current", "now")

       All the acceptable kinds besides a version str

       tag -- get the latest tagged version

       current or now -- get the current version from git. Most
       likely development version

    :ivar path:

       Default None. If None, assumes path is current working directory,
       otherwise provide the absolute path to the package base folder

    :vartype path: pathlib.Path | None
    :ivar is_use_final:

       Default False. ``final`` is not normally valid within a semantic
       version string. The use of final may be used to indicate intention of creating
       a tagged release version. If all the stars are aligned and its
       G'ds Will. If not, ``post release`` version(s) would occur and
       ``final`` would be incorrect.

       Don't create invalid semantic version strings cuz its convenient.
       Don't use this feature!

    :vartype is_use_final: typing.Any | None
    :raises:

       - :py:exc:`NotADirectoryError` -- Not the absolute path to package base folder

    """

    CURRENT_ALIAS_DEFAULT = "current"
    CURRENT_ALIASES = (
        "current",
        "now",
    )
    KINDS = ("tag", "current", "now")

    def __init__(
        self,
        path=None,
        is_use_final=False,
    ):
        super().__init__()

        self.path_cwd = path
        self.is_use_final = is_use_final

    @classmethod
    def sanitize_kind(cls, kind):
        """Allow kind to be a version str, 'current', 'tag'
        :param kind:

           Default None. If None, assumes "tag". Type of desired version str.
           Most reliable to pass in a version str if making a tagged
           version or want the tagged version. "current" will most likely
           get a development version

        :type kind: str | None
        :returns: kind ("current" or "tag") or a version str
        :rtype: str
        """

        def check_is_none(val):
            is_none = val is None
            if is_none:
                ret = "tag"
            else:  # pragma: no cover
                # N/A
                ret = val

            return ret

        def check_accidental_seq_str(val):
            """Accidentily pass in a Sequence[str] rather than an str"""
            is_seq_str_nonempty = (
                val is not None
                and isinstance(val, Sequence)
                and not isinstance(val, str)
                and len(val) != 0
                and isinstance(val[0], str)
            )
            if is_seq_str_nonempty:
                ret = val[0]
            else:
                # N/A
                ret = val

            return ret

        def check_seq_unsupported(val):
            is_seq_str_unsupported = (
                val is not None
                and isinstance(val, Sequence)
                and not isinstance(val, str)
                and len(val) != 0
                and not isinstance(val[0], str)
            )
            if is_seq_str_unsupported:
                ret = "tag"
            else:
                # N/A
                ret = val

            return ret

        def check_str(val):
            if val is not None and isinstance(val, str):
                if val not in cls.KINDS:
                    # Override version str
                    ret = val
                else:
                    if val in cls.CURRENT_ALIASES:
                        # current
                        ret = cls.CURRENT_ALIAS_DEFAULT
                    else:
                        # tag
                        ret = "tag"
            else:  # pragma: no cover
                # N/A
                ret = val

            return ret

        def check_unsupported(val):
            # fallback --> "tag". E.g. kind = 1.2345
            if val != "tag" and val != "current" and not isinstance(val, str):
                ret = "tag"
            else:  # pragma: no cover
                ret = val

            return ret

        kind_0 = check_is_none(kind)
        kind_1 = check_accidental_seq_str(kind_0)
        kind_2 = check_seq_unsupported(kind_1)
        kind_3 = check_str(kind_2)  # if still None
        kind_4 = check_unsupported(kind_3)

        return kind_4

    @property
    def path_cwd(self):
        """Getter for absolute Path to current working directory

        :returns: Absolute Path to current working directory
        :rtype: pathlib.Path
        """
        return self._path_cwd

    @path_cwd.setter
    def path_cwd(self, val):
        """Setter for cwd

        :param val: current working directory absolute Path
        :type val: typing.Any
        :raises:

           - :py:exc:`NotADirectoryError` -- Not the absolute path to package base folder

        """
        path_cwd = _path_or_cwd(val)
        if path_cwd.exists() and path_cwd.is_absolute() and not path_cwd.is_dir():
            msg_exc = "Not the absolute path to package base folder"
            raise NotADirectoryError(msg_exc)
        else:
            self._path_cwd = path_cwd

    @property
    def is_use_final(self):
        """Within a semantic version str "final" is not a valid token.
        However in scripts it might be used to indicate about to create a tagged version

        Use of final is discouraged

        :returns: True if final can be within a semantic version str otherwise False
        :rtype: bool
        """
        return self._is_use_final

    @is_use_final.setter
    def is_use_final(self, val):
        """Setter for is_use_final

        :param val: Should be a bool if not defaults to False
        :type val: typing.Any
        """
        if val is None or not isinstance(val, bool):
            self._is_use_final = False
        else:
            self._is_use_final = val

    @property
    def major(self):
        """major version. If breaking change, in API, should be incremented

        :returns: None if not called parse_ver beforehand. Otherwise will be an int
        :rtype: int | None
        """
        return self._major

    @property
    def minor(self):
        """minor version. Incremented if a new feature or a fix occurred

        :returns: None if not called parse_ver beforehand. Otherwise will be an int
        :rtype: int | None
        """
        return self._minor

    @property
    def micro(self):
        """micro version. For all the other possible categories of
        changes which are not exceptionally notable

        :returns: None if not called parse_ver beforehand. Otherwise will be an int
        :rtype: int | None
        """
        return self._micro

    @property
    def releaselevel(self):
        """Get long form: alpha, beta, candidate, post.
        Abbreviations (a, b, and rc) are converted into long forms:

        Pre-releases: alpha, beta, candidate, a, b, or rc

        Post release: post

        Does not indicate whether a development release or not

        :returns:

           pre-release (beta alpha) or release candidate (rc). None,
           if not call parse_var beforehand

        :rtype: str | None
        """
        return self._releaselevel

    @releaselevel.setter
    def releaselevel(self, val):
        """For release level, convert either short or long form into long form

        :param val: Either short or long release level str
        :type val: str
        """
        ret = val
        for long_, short_ in _map_release.items():
            if short_ == ret:
                ret = long_
            else:  # pragma: no cover continue
                pass
        self._releaselevel = ret

    @property
    def releaselevel_abbr(self):
        """Short form: a, b, rc, post

        :returns: Short form. Valid in semantic version str
        :rtype: str
        """
        long_form = self.releaselevel
        ret = long_form
        for long_, short_ in _map_release.items():
            if long_ == long_form:
                ret = short_

        return ret

    @property
    def serial(self):
        """Whether is a post release or not. Cannot be both a post and a pre release.

        :returns:

           1 indicates post release otherwise 0. None, if not call parse_var beforehand

        :rtype: int | None
        """
        return self._serial

    @property
    def dev(self):
        """Development version number

        :returns:

           dev version number. None is valid. If a dev starts from 0.
           Also None, if not call parse_var beforehand

        :rtype: int | None
        """
        return self._dev

    def parse_ver(self, ver):
        """Safely parses the semantic version str. The epoch and local
        will be removed.

        :param ver: version str. Best to preprocess this using sanitize_tag
        :type ver: str
        :raises:

           - :py:exc:`ValueError` -- Invalid version string. git
             requires one commit. setupttools-scm requires one tagged commit

        """
        # tuple[tuple[int, int, int, str, int], int]
        t_ver, dev = get_version(ver, is_use_final=self.is_use_final)
        # releaselevel is long form: post, candidate, alpha, beta
        # releaselevel could be in short form: a, b, rc
        major, minor, micro, releaselevel, serial = t_ver
        self._major = major
        self._minor = minor
        self._micro = micro
        self._releaselevel = releaselevel
        self._serial = serial
        self._dev = dev

    def version_xyz(self):
        """Get xyz version. Call parse_ver first

        :returns: xyz version str. Only None if parse_ver not called beforehand
        :rtype: str | None
        """
        is_major = (
            hasattr(self, "_major")
            and self._major is not None
            and isinstance(self._major, int)
            and self._major >= 0
        )
        is_minor = (
            hasattr(self, "_minor")
            and self._minor is not None
            and isinstance(self._minor, int)
            and self._minor >= 0
        )
        is_micro = (
            hasattr(self, "_micro")
            and self._micro is not None
            and isinstance(self._micro, int)
            and self._micro >= 0
        )

        if is_major and is_minor and is_micro:
            ret = f"{self._major}.{self._minor}.{self._micro}"
        else:
            ret = None

        return ret

    def anchor(self):
        """Full semantic version for display. xyz separated by hyphens

        :returns: None when parse_var has not been called otherwise version for display
        :rtype: str | None
        """
        xyz = self.version_xyz()
        if xyz is None:
            # Only None if parse_ver not called beforehand
            ret = None
        else:
            ret = xyz.replace(".", "-")

            # a, b, rc, post
            rel = self.releaselevel_abbr

            is_rel = rel is not None and isinstance(rel, str) and len(rel) != 0
            if is_rel and rel != "final":
                ret += f"{rel}{self.serial}"

        return ret

    def readthedocs_url(self, package_name, is_latest=False):
        """Get readthedocs.io URL. Call parse_ver first

        :param package_name:

           Differences from app name, contains hyphens rather than underscores

        :param is_latest:

           Default False. If True get latest url otherwise get version specific url

        :type is_latest: bool | None
        :returns:

           url to readthedocs.io for a semantic version of the docs, not
           necessarily the latest

        :rtype: str
        """
        # app-name --> package_name
        if "_" in package_name:
            package_name = package_name.replace("_", "-")
        else:  # pragma: no cover
            pass

        if is_latest is None or not isinstance(is_latest, bool):
            bol_is_latest = False
        else:
            bol_is_latest = is_latest

        if bol_is_latest is True:
            ver_ = "latest"
        else:
            ver_ = self.version_xyz()
            if ver_ is None:
                ver_ = "latest"
            else:  # pragma: no cover
                pass

        ret = f"https://{package_name}.readthedocs.io/en/{ver_}"

        return ret

    def version_clean(self, kind, package_name=None):
        """Gets cleaned version str from git

        Override by passing in a version str

        - "current" or "now"
          Gets current version thru setuptools-scm

        - "tag"
          Gets the last tagged version. Uses :command:`git describe --tag`

        - a version str
          Uses that version str. Use this to create prerelease, post
          release, and tagged versions

        :param kind: a known kind or a version str
        :type kind: str
        :param package_name:

           Default None. Package name so as to avoid getting it from git

        :type package_name: str | None
        :returns: cleaned version str
        :rtype: str
        :raises:

           - :py:exc:`AssertionError` -- Could not get package name from git

           - :py:exc:`SetuptoolsSCMNoTaggedVersionError` -- Neither a
             tagged version nor a first commit. Create a commit and
             preferrably a tagged version

           - :py:exc:`ValueError` -- Explicit version str invalid

        """
        cls = type(self)
        msg_exc = (
            "Neither a tagged version nor a first commit. "
            "Make first commit. Preferrably a tagged version"
        )

        # sanitize again just in case
        # returns: current, tag, or version str
        kind_: str = cls.sanitize_kind(kind)

        if kind_ not in cls.KINDS:
            # Version str. Will become next version
            git_ver = kind_
            try:
                clean_ver = sanitize_tag(git_ver)
            except ValueError:
                self._version = None
                raise
        else:
            # Don't sanitize. Affects src/[project name]/_version.py
            # Automagically written by setuptools-scm. Version -- git
            if kind_ == cls.CURRENT_ALIAS_DEFAULT:
                # Most likely development version
                func = partial(_current_version, path=self.path_cwd)
                git_ver = func()
                if git_ver is None:
                    self._version = None
                    # No current version only happens when no first commit
                    raise SetuptoolsSCMNoTaggedVersionError(msg_exc)
                else:  # pragma: no cover
                    # Do nothing
                    pass
            else:
                """last tagged version. May throw AttributeError if
                cannot get package_name"""
                func = partial(
                    _tag_version,
                    path=self.path_cwd,
                    package_name=package_name,
                )
                git_ver = func()
                if git_ver is None:
                    # No tagged version. Fallback to current version
                    func = partial(_current_version, path=self.path_cwd)
                    git_ver = func()
                    if git_ver is None:
                        self._version = None
                        """Neither a tagged version nor a first commit.
                        Definitely raise warning"""
                        raise SetuptoolsSCMNoTaggedVersionError(msg_exc)
                    else:  # pragma: no cover
                        # Do nothing
                        pass
                else:
                    pass
            clean_ver = sanitize_tag(git_ver)

        self._version = clean_ver

        # w/o final
        return clean_ver

    @property
    def __version__(self):
        """Cleaned version available after call to version_clean

        :returns: Cleaned version or None if version_clean has not been called
        :rtype: str | None
        """
        return self._version
