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
   :type: tuple[str, str, str]
   :value: ("SemVersion", "sanitize_tag", "get_version")

   Module exports

.. py:data:: _map_release
   :type: types.MappingProxyType[str, str]
   :value: types.MappingProxyType({"alpha": "a", "beta": "b", "candidate": "rc"})

   Mapping of release levels. So can gracefully go back and forth

   Read only mapping. key is long name. value is abbreviation. Long
   names will be converted into the abbreviations

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

import importlib.util
import logging
import sys
import types
import warnings
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

from ._package_installed import is_package_installed
from ._run_cmd import run_cmd
from ._safe_path import (
    fix_relpath,
    resolve_path,
)
from .parser_in import TomlParser
from .version_file._overrides import (
    PRETEND_KEY_NAMED,
    normalize_dist_name,
)

__package__ = "drain_swamp"
__all__ = (
    "SemVersion",
    "sanitize_tag",
    "get_version",
)

_map_release = types.MappingProxyType({"alpha": "a", "beta": "b", "candidate": "rc"})
_logger = logging.getLogger("drain_swamp.version_semantic")


def _path_or_cwd(val):
    """Frequently used and annoying to test multiple times.

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


def get_package_name(path):
    """Get package name, unmodified, from ``pyproject.toml``.

    :param path: absolute path to either package base folder or ``pyproject.toml``
    :type path: pathlib.Path
    :returns:

       package name. ``[project].name`` is a required field, so can
       assume exists. None if issue with ``pyproject.toml``

    :rtype: str | None
    """
    path_ = _path_or_cwd(path)
    tp = TomlParser(path_)
    d_pyproject_toml = tp.d_pyproject_toml
    if d_pyproject_toml is not None:
        ret = d_pyproject_toml.get("project", {}).get("name", None)
    else:
        ret = None

    return ret


def _scm_key(dist_name):
    """Environment variable offer by setuptools-scm to set a specific version.
    Acts as an normal behavior override.

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
    # source setuptools_scm._override.read_named_env
    env_var_dist_name = normalize_dist_name(dist_name)
    d_named = {"name": env_var_dist_name}
    scm_override_key = PRETEND_KEY_NAMED.format(**d_named)

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

    executable_path = resolve_path("git")
    cmd = (executable_path, "describe", "--tag")
    t_ret = run_cmd(cmd, cwd=path_cwd)
    out, err, exit_code, exc = t_ret
    if exc is not None:
        # git says, no tagged version
        str_out = None
    else:
        # No tags yet
        # 128 -- fatal: No names found, cannot describe anything.
        is_fail = exit_code != 0
        if not is_fail:
            str_out = out
        else:
            str_out = None

    return str_out


def _strip_epoch(ver):
    """Strip epoch.

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
    """Strip local from end of version string.

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


def _is_ver_ok(str_v):
    """Check version str ok.

    :param str_v: raw version str
    :type str_v: str
    :returns: True if semantic version str is valid otherwise False
    :rtype: bool
    """
    try:
        Version(str_v)
    except InvalidVersion:
        ret = True
    else:
        ret = False

    return ret


def sanitize_tag(ver):
    """Avoid reinventing the wheel, leverage Version.

    ``final`` is invalid.

    :param ver: raw semantic version
    :type ver: str
    :returns: Sanitized semantic version str
    :rtype: tuple[str, str | None]
    :raises:

       - :py:exc:`ValueError` -- Invalid token within Version str

    """
    # Careful! Will choke on initial untagged version, e.g. ``0.1.dev0.d20240213``
    str_remaining_whole = _remove_v(ver)

    # Strip epoch, if exists
    _, str_remaining_stripped = _strip_epoch(str_remaining_whole)

    """Strip local, if exists

    Will fail to detect an initial untagged version e.g. '0.1.dev0.d20240213'"""
    local, str_remaining_stripped = _strip_local(str_remaining_stripped)

    # fix candidate --> rc
    # '0.1.1.candidate1dev1+g4b33a80.d20240129' --> '0.1.1rc1.dev1+g4b33a80.d20240129'
    if "candidate" in str_remaining_whole:
        str_remaining_whole = str_remaining_whole.replace("candidate", "rc")
        is_problem = _is_ver_ok(str_remaining_whole)
    else:  # pragma: no cover
        is_problem = _is_ver_ok(str_remaining_whole)

    # '0.1.dev0.d20240213' --> '0.1.dev0'
    if is_problem:
        lst = str_remaining_whole.split(".")
        ver_try = ".".join(lst[:-1])

        is_still_issue = _is_ver_ok(ver_try)
    else:  # pragma: no cover
        # Do nothing
        is_still_issue = False

    if is_still_issue:
        try:
            v = Version(str_remaining_whole)
        except InvalidVersion as e:
            msg = f"Version contains invalid token. {e}"
            raise ValueError(msg) from e
    else:  # pragma: no cover
        # Do nothing
        pass

    v = Version(str_remaining_whole)
    ret = str(v)

    # Strip epoch and local, if exists
    _, ret = _strip_epoch(ret)
    _, ret = _strip_local(ret)

    return ret, local


def _pre_split(_v):
    """Force short prerelease.

    short: a, b, or rc
    long: alpha, beta, candidate

    :param _v: packaging module Version class
    :type _v: packaging.version.Version
    :returns: short prerelease string and prerelease number
    :rtype: tuple[str, int, str] | None
    """
    t_pre = _v.pre
    if t_pre is None:
        ret = None
    else:
        short = t_pre[0]
        serial = t_pre[1]
        ret_short = None
        ret_long = None

        # ret_short means we recognize the short form, regardless of Version's opinion
        for _, short_ in _map_release.items():
            if short_ == short:
                ret_short = short_
            else:  # pragma: no cover
                pass

        if ret_short is None:  # pragma: no cover
            # unrecognized short
            ret = None
            pass
        else:  # pragma: no cover
            for long_, short_ in _map_release.items():
                if ret_short == short_:
                    if long_ != "candidate":
                        ret_long = long_
                    else:
                        # candidate is not a valid semantic version component
                        ret_long = short_
                else:  # pragma: no cover
                    pass
            ret = (ret_long, serial, ret_short)

    return ret


def get_version(ver, is_use_final=False):
    """Semantic version string broken into parts.

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
        # not prereleases and not post
        # ``final`` means intend to bump version. Not actually valid
        releaselevel = "" if not is_use_final else "final"
        serial = 0
        _dev = None
    elif _v.is_prerelease and not _v.is_postrelease:
        # prereleases and not post
        # Requires long
        t_pre = _pre_split(_v)
        if t_pre is None:
            # dev
            serial = 0
            releaselevel = ""
        else:
            ver_long, serial, ver_short = t_pre
            # alpha beta, candidate, a, b, or rc
            # ver_long: candidate --> rc
            ver_long, serial, ver_short = _pre_split(_v)
            releaselevel = ver_long
    elif not _v.is_prerelease and _v.is_postrelease:
        # post
        releaselevel = "post"
        serial = _v.post
    else:
        # prerelease and post. May or may not be dev release
        t_pre = _pre_split(_v)
        if t_pre is None:
            # 1.4.0.post1.dev0
            releaselevel = "post"
            serial = _v.post
        else:
            # 1.2.3rc1.post0.dev9
            # Keep the prerelease and lose the post details
            ver_long, serial, ver_short = t_pre
            releaselevel = ver_long

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
    if not is_package_installed("setuptools-scm"):
        return None
    else:  # pragma: no cover
        pass

    # Call in subprocess to avoid circular import error
    # Replaces:
    # cmd = [sys.executable, "setup.py", "--version"]
    # cmd = [sys.executable, "-m", "setuptools_scm"]
    if is_package_installed("drain_swamp"):
        # thru entrypoint
        cmd = ("scm-version", "get")
    else:  # pragma: no cover
        # thru pep366. unittest adds nothing
        f_relpath = fix_relpath("src/drain_swamp/cli_scm_version.py")
        cmd = (sys.executable, f_relpath, "get")

    t_ret = run_cmd(cmd, cwd=path_cwd)
    out, err, exit_code, exc = t_ret
    if exc is not None:
        # scm-version get says no tagged version
        str_out = None
    else:
        is_fail = exit_code != 0
        if not is_fail:
            str_out = out
        else:
            str_out = None

    return str_out


def _tag_version(
    next_version="",
    path=None,
):
    """Previously meant latest git tagged version, but there is no
    situation where this is desirable.

    If ``tag`` version, take from: version_file, or fallback
    If version provided, update version file

    :param next_version: Default empty string. If not provided, tagged version
    :type next_version: str | None
    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :returns: tagged version or current version str
    :rtype: str | None
    :meta private:
    :raises:

       - :py:exc:`AssertionError` -- ``pyproject.toml`` missing or unparsable

    """
    # empty str means take current tag version
    ret = _arbritary_version(next_version, path=path)

    return ret


def _arbritary_version(
    next_version,
    path=None,
):
    """From the version file get semantic version str. This depends heavily on
    ``pyproject.toml`` being well-formed

    :param next_version: Default empty string. If not provided, tagged version
    :type next_version: str
    :param path:

       Default None. If None assumes path is current working directory,
       otherwise provide the path to the package base folder

    :type path: pathlib.Path | None
    :returns: tagged version or current version str. None rather than empty string
    :rtype: str | None
    :meta private:

    .. warning::

       This command writes to src/[package name]/_version.py
       Use :py:func:`unittest.mock.patch` to avoid the actual call

    """
    msg_issue = "Could not get tag version from version_file"
    path_cwd = _path_or_cwd(path)

    tp = TomlParser(path_cwd)
    d_pyproject_toml = tp.d_pyproject_toml
    if d_pyproject_toml is None:
        msg_warn = f"Issue with pyproject.toml, {msg_issue}"
        _logger.warning(msg_warn)
        raise AssertionError(msg_warn)
    else:  # pragma: no cover
        path_f = tp.path_file
        path_package_base = path_f.parent

    """From here, for all issues, issue a non-blocking warning and return None.
    This strategy is so can fallback to the current version"""
    lst_dynamic = d_pyproject_toml.get("project", {}).get("dynamic", [])
    is_version_file = isinstance(lst_dynamic, Sequence) and "version" in lst_dynamic
    static_ver = d_pyproject_toml.get("project", {}).get("version", None)
    is_version_static = (
        static_ver is not None
        and isinstance(static_ver, str)
        and len(static_ver.strip()) != 0
    )
    if is_version_static:
        # static version
        ver_tag = d_pyproject_toml.get("project", {}).get("version", None)
    elif is_version_file:
        # dynamic version_file
        d_dynamic = (
            d_pyproject_toml.get("tool", {}).get("setuptools", {}).get("dynamic", {})
        )

        is_version = (
            "version" in d_dynamic.keys()
            and isinstance(d_dynamic["version"], dict)
            and (
                "attr" in d_dynamic["version"].keys()
                or "file" in d_dynamic["version"].keys()
            )
        )

        # Check tool.setuptools.dynamic.version
        if not is_version:  # pragma: no cover
            msg_warn = (
                "Expecting tool.setuptools.dynamic.version to contain "
                f"attr or file key, {msg_issue}"
            )
            warnings.warn(msg_warn)
            return None
        else:  # pragma: no cover
            pass

        d_version = d_dynamic["version"]
        is_attr = "attr" in d_version.keys() and isinstance(d_version["attr"], str)
        is_file = "file" in d_version.keys() and isinstance(d_version["file"], str)
        if is_attr:
            # https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html
            # ast.literal_eval() ??
            # attr is dotted path to module variable containing semantic version str
            # file would be to a text file
            version_file_dottedpath = d_dynamic["version"]["attr"]
            dots = version_file_dottedpath.split(".")
            variable_name = dots[-1]
            dotted_path_to_module = dots[:-1]

            # this is an assumption
            # ############################################################################################
            lst_relpath = ["src"]

            lst_relpath.extend(dotted_path_to_module)

            # Coming from a dotted_path, restore the suffix
            file_stem = Path(lst_relpath[-1]).stem
            lst_relpath[-1] = f"{file_stem!s}.py"

            path_version_file = path_package_base.joinpath(*lst_relpath)
            is_not_file = not (
                path_version_file.exists()
                and path_version_file.is_file()
                and path_version_file.suffixes == [".py"]
            )
            if is_not_file:
                msg_warn = (
                    f"version_file {path_version_file} either does "
                    f"not exist or not a file, {msg_issue}"
                )
                warnings.warn(msg_warn)
                return None
            else:  # pragma: no cover
                name = path_version_file.stem
                spec = importlib.util.spec_from_file_location(
                    name,
                    path_version_file,
                )
                module = importlib.util.module_from_spec(spec)
                loader = importlib.util.LazyLoader(spec.loader)
                loader.exec_module(module)
                mixed_var = getattr(module, variable_name, None)
                if mixed_var is None or not isinstance(mixed_var, str):
                    msg_warn = (
                        "In version_file (python module), "
                        f"{path_version_file} module  variable, "
                        "__version__ expected to be a the semantic "
                        "version str, unsupported type got "
                        f"{type(mixed_var)} {msg_issue}"
                    )
                    warnings.warn(msg_warn)
                    return None
                else:  # pragma: no cover
                    pass
                ver_tag = mixed_var
        elif is_file:
            path_f = path_package_base.joinpath(d_version["file"])
            _logger.info(f"_tag_version dynamic version file: {path_f}")
            is_not_file = not (
                path_f.exists() and path_f.is_file() and path_f.suffixes == [".txt"]
            )
            if is_not_file:
                msg_warn = (
                    "Could not find version_file "
                    f"""{d_version["file"]} {msg_issue}"""
                )
                warnings.warn(msg_warn)
                return None
            else:  # pragma: no cover
                pass

            # limit read size to avoid bufferoverflow attack
            # ###############################################################################################
            ver_tag = path_f.read_text()
        else:  # pragma: no cover
            # Check tool.setuptools.dynamic.version.[file|attr] value valid
            msg_warn = (
                "marked dynamic, tool.setuptools.dynamic.version.[file|attr] "
                f"contains something other than a str. {msg_issue}"
            )
            warnings.warn(msg_warn)
            return None
    else:
        msg_warn = (
            f"In {path_f}, neither static nor dynamic version specified "
            f"pyproject.toml is invalid. {msg_issue}"
        )
        warnings.warn(msg_warn)
        return None

    return ver_tag


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

    executable_path = resolve_path("git")
    cmd = (
        executable_path,
        "rev-parse",
        "--show-toplevel",
    )
    t_ret = run_cmd(cmd, cwd=path_cwd)
    out, err, exit_code, exc = t_ret
    if exc is not None:
        ret = None
    else:
        if out is None:
            ret = None
        else:
            str_mixed = Path(out).name
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
        """Class constructor."""
        super().__init__()

        self.path_cwd = path
        self.is_use_final = is_use_final

    @classmethod
    def sanitize_kind(cls, kind):
        """Allow kind to be a version str, 'current', 'tag'.

        :param kind:

           Default None. If None, assumes ``"tag"``. Type of desired version str.
           Most reliable to pass in a version str if making a tagged
           version or want the tagged version. "current" will most likely
           get a development version

        :type kind: str | None
        :returns: kind ("current" or "tag") or a version str
        :rtype: str
        """

        def check_is_none(val):
            """Check if is None. If None, return ``"tag"``.

            :param val: Can be anything.
            :type val: typing.Any
            :returns: non-None Any.
            :rtype: str | typing.Any
            """
            is_none = val is None
            if is_none:
                ret = "tag"
            else:  # pragma: no cover
                # N/A
                ret = val

            return ret

        def check_accidental_seq_str(val):
            """Accidentily pass in a Sequence[str] rather than an str.

            :param val: Possibly a Sequence[str] or a str
            :type val: typing.Any
            :returns: If not a str, take the first sequence item.
            :rtype: str
            """
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
            """Check sequence. Should contain non-empty str.

            :param val: Value to check
            :type val: typing.Any
            :returns: "tag" if unsupported otherwise val
            :rtype: str
            """
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
            """Check if a kind, otherwise return as is.

            :param val: Any possible value
            :type val: typing.Any
            :returns: A Kind or return as is.
            :rtype: str
            """
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
            """Check unsupported data type.

            :param val: Any possible value
            :type val: typing.Any
            :returns: A Kind. Default ``"tag"``
            :rtype: str
            """
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
        """Getter for absolute Path to current working directory.

        :returns: Absolute Path to current working directory
        :rtype: pathlib.Path
        """
        return self._path_cwd

    @path_cwd.setter
    def path_cwd(self, val):
        """Setter for cwd.

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
        """Setter for is_use_final.

        :param val: Should be a bool if not defaults to False
        :type val: typing.Any
        """
        if val is None or not isinstance(val, bool):
            self._is_use_final = False
        else:
            self._is_use_final = val

    @property
    def major(self):
        """major version. If breaking change, in API, should be incremented.

        :returns: None if not called parse_ver beforehand. Otherwise will be an int
        :rtype: int | None
        """
        return self._major

    @property
    def minor(self):
        """minor version. Incremented if a new feature or a fix occurred.

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
        """For release level, convert either short or long form into long form.

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
        """Short form: a, b, rc, post.

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
        """Development version number.

        :returns:

           dev version number. None is valid. If a dev starts from 0.
           Also None, if not call parse_var beforehand

        :rtype: int | None
        """
        return self._dev

    @property
    def release(self):
        """Components of the release segment of the version.

        Does not include epoch or any pre-release / development / post-release
        suffixes

        :returns: tuple of major, minor, micro
        :rtype: tuple[int, int, int]
        """
        return self._release

    @staticmethod
    def as_tuple(version_str):
        """version tuple as written to ``_version.py`` file.

        :param version_str: raw version str
        :type version_str: str
        :returns: version tuple
        :rtype: tuple[int | str, ...]
        """
        try:
            ver, local = sanitize_tag(version_str)
        except ValueError:
            return (version_str,)

        sv = SemVersion()
        sv.parse_ver(ver, local=local)

        version_fields: tuple[int | str, ...] = sv.release

        if sv.dev is not None:
            version_fields += (f"dev{sv.dev}",)
        else:  # pragma: no cover
            pass

        if sv._local is not None:
            version_fields += (sv._local,)
        else:  # pragma: no cover
            pass

        return version_fields

    def parse_ver(self, ver, local=None):
        """Safely parses the semantic version str. The epoch and local
        will be removed.

        :param ver: version str. Best to preprocess this using sanitize_tag
        :type ver: str
        :param local:

           Default None. local format ``+g[commit].d[YYYYMMDD]``.
           Format wrong if there isn't minimum one tagged version

        :type local: str | None
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
        if local is None:  # pragma: no cover
            self._local = None
        else:
            is_unsupported = not isinstance(local, str)
            is_empty_str = isinstance(local, str) and len(local.strip()) == 0
            if is_unsupported or is_empty_str:  # pragma: no cover
                self._local = None
            else:
                self._local = local

        self._release = (major, minor, micro)

    def version_xyz(self):
        """Get xyz version. Call parse_ver first.

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
        """Full semantic version for display. xyz separated by hyphens.

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
        """Get readthedocs.io URL. Call parse_ver first.

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

    def version_clean(self, kind):
        """Gets cleaned version str from either git or version_file.

        - "current" or "now"
          Gets current version thru setuptools-scm

        - "tag"
          Gets version from version file. Greatly depends on the
          ``pyproject.toml`` being valid and well configured.

          If ``pyproject.toml`` doesn't exist or malformed will raise a
          :py:exc:`AssertionError`. For any other reason, will issue a
          warning and return None.

          Prefer to fallback to the current version rather than not be
          able to return a version str at all. Convert the
          warning --> strerr, so have a chance to correct the problem
          without sacrificing usability

        - a version str
          Uses that version str. Use this to create prerelease, post
          release, and tagged versions

        :param kind: a known kind or a version str
        :type kind: str
        :returns: cleaned version str
        :rtype: str
        :raises:

           - :py:exc:`AssertionError` -- ``pyproject.toml`` missing or malformed

           - :py:exc:`ValueError` -- Explicit version str invalid

        """
        cls = type(self)

        # sanitize again just in case
        # returns: current, tag, or version str
        kind_: str = cls.sanitize_kind(kind)

        if kind_ not in cls.KINDS:
            # Version str. Will become next version
            git_ver = kind_
            try:
                clean_ver, local = sanitize_tag(git_ver)
            except ValueError:
                self._version = None
                raise
        else:
            # Don't sanitize. Affects src/[project name]/_version.py
            # Automagically written by setuptools-scm. Version -- git
            if kind_ == cls.CURRENT_ALIAS_DEFAULT:
                """Most likely development version
                No git init, current version --> "0.0.1"
                """
                func = partial(_current_version, path=self.path_cwd)
                git_ver = func()
            else:
                """last tagged version. May throw AttributeError if
                has pyproject.toml configuration issues"""
                func = partial(
                    _tag_version,
                    path=self.path_cwd,
                )
                git_ver = func()
                # Check -- version file semantic version str
                if git_ver is not None:
                    try:
                        sanitize_tag(git_ver)
                    except ValueError:
                        # invalid semantic version str in version file
                        git_ver = None
                else:  # pragma: no cover
                    pass

                if git_ver is None:
                    """No tagged version. Fallback to current version.
                    No git init, current version --> "0.0.1"
                    """
                    func = partial(_current_version, path=self.path_cwd)
                    git_ver = func()
                else:  # pragma: no cover
                    pass

            clean_ver, local = sanitize_tag(git_ver)

        self._version = clean_ver

        # w/o final
        return clean_ver

    @property
    def __version__(self):
        """Cleaned version available after call to version_clean.

        :returns: Cleaned version or None if version_clean has not been called
        :rtype: str | None
        """
        return self._version
