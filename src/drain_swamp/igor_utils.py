"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

``igor.py`` utils

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: __all__
   :type: tuple[str, str, str, str, str, str, str]
   :value: ("seed_changelog", "edit_for_release", "build_package", "pretag", "print_cheats", "get_tag_version", "write_version_file")

   Module level exports

.. py:data:: SCRIV_START
   :type: str
   :value: ".. scriv-start-here\\n\\n"

   In ``CHANGES.rst``, token beneath which a changelog entry is written

.. py:data:: UNRELEASED
   :type: str
   :value: "Unreleased\\n----------"

   Written into ``CHANGES.rst``, the start of what is being called, the seed

.. py:data:: REGEX_COPYRIGHT_LINE
   :type: str

   ``NOTICE.txt`` has a start and end year. Regex for grabbing both.

.. py:data:: COPYRIGHT_START_YEAR_FALLBACK
   :type: int
   :value: 1970

   Fallback start year. ``NOTICE.txt`` start year gets updated. Since the
   start year is static expected to be provided in ``pyproject.toml``

"""

import os
import re
import subprocess
import sys
from pathlib import (
    Path,
    PurePath,
)

from ._run_cmd import run_cmd
from .check_type import is_ok
from .package_metadata import PackageMetadata
from .parser_in import TomlParser
from .snippet_sphinx_conf import SnipSphinxConf
from .version_file.dump_version import write_version_files
from .version_semantic import (
    SemVersion,
    _current_version,
    _path_or_cwd,
    _scm_key,
    get_package_name,
    sanitize_tag,
)

__all__ = (
    "seed_changelog",
    "edit_for_release",
    "build_package",
    "pretag",
    "print_cheats",
    "get_tag_version",
    "write_version_file",
)
__package__ = "drain_swamp"

UNRELEASED = "Unreleased\n----------"
SCRIV_START = ".. scriv-start-here\n\n"
COPYRIGHT_START_YEAR_FALLBACK = 1970
REGEX_COPYRIGHT_LINE = r"Copyright {0}.*? {1}"


def update_file(fname, pattern, replacement):
    """Update the contents of a file, replacing pattern with replacement.

    :param fname: str absolute path
    :type fname: str
    :param pattern: regex pattern
    :type pattern: str
    :param replacement: replacement text after regex substitution
    :type replacement: str

    .. todo:: check have r/w permissions

       Did not check file permissions

    """
    is_path_or_str = is_ok(fname) or issubclass(type(fname), PurePath)
    if not is_path_or_str:
        msg_exc = f"Expected a non-empty str path or Path got {fname}"
        print(msg_exc, file=sys.stderr)
        return

    try:
        path_file = Path(fname)
    except Exception:  # pragma: no cover
        path_file = None

    is_absolute_file = (
        path_file is not None and path_file.exists() and path_file.is_file()
    )
    if is_absolute_file:
        # Assumes r/w permissions
        old_text = path_file.read_text()

        new_text = re.sub(pattern, replacement, old_text, count=1)

        if new_text != old_text:
            msg_info = f"Updating {fname}"
            print(msg_info, file=sys.stderr)

            path_file.write_text(new_text)
        else:  # pragma: no cover
            # Do nothing
            pass
    else:
        msg_exc = f"Provide an absolute path to a file. Got, {fname}"
        print(msg_exc, file=sys.stderr)
        return


def seed_changelog(path_cwd):
    """Add a new empty changelog entry

    :param path_cwd: Current working directory path
    :type path_cwd: pathlib.Path
    :returns:

       0 success
       1 missing start token
       2 file not found or permissions issue

    :rtype: int
    """
    path_changelog = path_cwd.joinpath("CHANGES.rst")
    pattern = re.escape(SCRIV_START)
    replacement = f"{UNRELEASED}\n\nNothing yet.\n\n\n" + SCRIV_START

    # Check if pattern exists
    if not (path_changelog.exists() and path_changelog.is_file()):
        msg_warn = f"Provide an absolute path to a file. Got, {path_changelog!s}"
        print(msg_warn, file=sys.stderr)
        ret = 2
    else:
        contents = path_changelog.read_text()

        prog = re.compile(pattern)
        lst_matches = re.findall(prog, contents)
        if len(lst_matches) == 0:
            msg_warn = (
                f"Start token not found. In CHANGES.rst, add token, {SCRIV_START}"
            )
            print(msg_warn, file=sys.stderr)
            ret = 1
        else:
            # prints "Updating " to stderr
            update_file(
                path_changelog,
                pattern,
                replacement,
            )
            ret = 0

    return ret


def edit_for_release(path_cwd, kind, snippet_co=None):
    """Edit a few files in preparation for a release.

    .. code-block:: text

       [tool.drain-swamp]
       copyright_start_year = [an int]

    app name also taken from pyproject.toml

    :param path_cwd: Current working directory path
    :type path_cwd: pathlib.Path
    :param kind:

       version str, "tag", or "current" or "now". For tagged versions, a version str

    :type kind: str
    :param snippet_co:

       Default None. Sphinx conf.py snippet code

    :type snippet_co: str
    :returns:

       None if no error occurred. 3 if no folder, 4 if no doc?/conf.py
       file. 2 version str was dodgy

    :rtype: int | None
    """
    # user input parsing?
    path_changelog = path_cwd.joinpath("CHANGES.rst")
    path_notice_txt = path_cwd.joinpath("NOTICE.txt")

    try:
        sc = SnipSphinxConf(path=path_cwd)
    except NotADirectoryError:
        msg_exc = "Expected a doc/ or docs/ folder"
        print(msg_exc, file=sys.stderr)
        return 3
    except FileNotFoundError:
        # if no doc?/conf.py ... do nothing
        msg_exc = "As an optimization, doc?/conf.py is needed. It can be an empty file"
        print(msg_exc, file=sys.stderr)
        return 4

    # sc.path_cwd if already filtered
    # ensure app name is not a possible package, so pyproject.toml is loaded
    pm = PackageMetadata(UNRELEASED, path=sc.path_cwd)
    d_pyproject_toml = pm.d_pyproject_toml

    # Get copyright_start_year from pyproject.toml
    d_section = d_pyproject_toml.get("tool", {}).get("drain-swamp", {})
    if "copyright_start_year" in d_section.keys() and (
        isinstance(d_section["copyright_start_year"], int)
        or isinstance(d_section["copyright_start_year"], str)
    ):
        try:
            copyright_start_year = int(d_section["copyright_start_year"])
        except Exception:
            """alternative is to get as a command option, but that would
            be tedious to provide every time"""
            copyright_start_year = COPYRIGHT_START_YEAR_FALLBACK
    else:
        copyright_start_year = COPYRIGHT_START_YEAR_FALLBACK

    # Get app name from pyproject.toml
    project_name = d_pyproject_toml.get("project", {}).get("name", None)
    if project_name is not None and isinstance(project_name, str):
        package_name = project_name.replace("-", "_")
    else:
        package_name = None

    # After call, will have sc.SV and sc.author_name_left
    try:
        sc.contents(
            kind,
            package_name,
            copyright_start_year,
        )
    except (AssertionError, ValueError) as e:
        msg_exc = str(e)
        print(msg_exc, file=sys.stderr)
        return 2

    """No feedback if ``doc?/conf.py`` encounters:

    - ReplaceResult.VALIDATE_FAIL

    - ReplaceResult.NO_MATCH

    """
    sc.replace(snippet_co=snippet_co)
    author_first_name = sc.author_name_left

    is_dev = sc.SV.dev is not None and isinstance(sc.SV.dev, int)
    if is_dev:
        msg_info = f"**\n** This is a dev release: {sc.SV.__version__}\n**\n\nNo edits"
        print(msg_info, file=sys.stderr)
        return

    # NOTICE.txt
    regex_pattern = REGEX_COPYRIGHT_LINE.format(
        str(copyright_start_year),
        author_first_name,
    )
    str_year_end = SnipSphinxConf.now_to_str("%Y")
    str_dt_ymd = SnipSphinxConf.now_to_str("%Y-%m-%d")

    replace_with = f"Copyright {0}-{1} {author_first_name}".format(
        str(copyright_start_year),
        str_year_end,
        author_first_name,
    )
    update_file(path_notice_txt, regex_pattern, replace_with)

    # CHANGES.rst
    ver = sc.SV.__version__
    anchor = sc.SV.anchor()
    if ver is not None and anchor is not None:
        title = f"Version {ver} — {str_dt_ymd}"
        rule = "-" * len(title)
        new_head = f".. _changes_{anchor}:\n\n{title}\n{rule}"

        pairs = (
            (re.escape(SCRIV_START), ""),
            (re.escape(UNRELEASED), f"{SCRIV_START}{new_head}"),
        )

        for pattern, replacement in pairs:
            update_file(path_changelog, pattern, replacement)
        else:  # pragma: no cover
            pass
    else:  # pragma: no cover
        pass


def get_version_file_path(path):
    """Get version file relative path, from pyproject.toml,
    tool.pipenv-unlock.version_file

    :param path: absolute path to either package base folder or ``pyproject.toml``
    :type path: pathlib.Path
    :returns:

       version file relative path. Relative to package base path. None
       if issue with ``pyproject.toml``

    :rtype: str | None
    """
    path_ = _path_or_cwd(path)
    tp = TomlParser(path_)
    d_pyproject_toml = tp.d_pyproject_toml
    if d_pyproject_toml is not None:
        ret = (
            d_pyproject_toml.get("tool", {})
            .get("pipenv-unlock", {})
            .get("version_file", None)
        )
    else:
        ret = None

    return ret


class AlterEnv:
    """setuptools thin wrapped build-backend will need to modify the
    in-process environment to inform setuptools-scm which version to use.

    That will mean getting the key / value only via subprocess to an
    pep366 compliant entrypoint

    :ivar path: Current working directory path
    :vartype path: pathlib.Path
    :ivar kind:

       version str, "tag", or "current" or "now". For tagged versions, a version str

    :vartype kind: str
    :raises:

       - :py:exc:`NotADirectoryError` -- cwd is not a folder

       - :py:exc:`AssertionError` -- Could not get package name from pyproject.toml

       - :py:exc:`ValueError` -- Explicit version str invalid

    """

    __slots__ = (
        "_path_cwd",
        "_pkg_name",
        "_scm_override_val",
        "_scm_override_key",
        "_version_file",
    )

    def __init__(self, path, kind):
        """Class constructor."""
        super().__init__()
        try:
            sv = SemVersion(path=path)
        except (NotADirectoryError, FileNotFoundError) as e:
            msg_exc = f"Expecting a folder path. Got a file {path}.\n{str(e)}"
            raise NotADirectoryError(msg_exc) from e

        try:
            # fallback version "0.0.1"
            # afterwards path available as sv.path_cwd
            ver = sv.version_clean(kind)
        except AssertionError:
            """Has pyproject.toml configuration issues or version file is bad
            Test: kind="tag", package_name="asdfasfsadfasdfasdf"
            """
            raise
        except ValueError:
            """Explicit version str invalid. Either from version_file,
            scm (aka git), or explicit e.g. kind='golf balls'"""
            raise

        self._path_cwd = sv.path_cwd
        self._scm_override_val = ver

        pkg_name = get_package_name(path)
        if pkg_name is None:
            msg_exc = "Could not get package name from pyproject.toml"
            raise AssertionError(msg_exc)
        else:  # pragma: no cover
            pass
        self._pkg_name = pkg_name

        self.scm_key = _scm_key(pkg_name)

        # TypeError or ValueError --> AssertionError
        version_file = get_version_file_path(path)
        try:
            self.version_file = version_file
        except TypeError as e:
            msg_warn = "Expecting a relative path to version file"
            raise AssertionError(msg_warn) from e

    def modify_env(self):
        """Get a modified :py:data:`os.environ`.

        Alter environment so setuptools-scm knows what the version should be

        :returns: Modified os.environ Pass to a subprocess
        :rtype: os.Environ[typing.Any]
        """
        env = os.environ.copy()
        env |= {self.scm_key: self.scm_val}

        return env

    @property
    def path_cwd(self):
        """Current working directory path.

        SemVersion does a good job at user input validation

        :returns: cwd path
        :rtype: pathlib.Path
        """
        return self._path_cwd

    @property
    def scm_key(self):
        """Get setuptools-scm key.

        :returns: setuptools-scm key for forcing a particular version
        :rtype: str
        """
        return self._scm_override_key

    @scm_key.setter
    def scm_key(self, val):
        """Setter for scm_key. Ensure upper case and underscore, not hyphen.

        :param val: Value to be set
        :type val: typing.Any
        """
        if val is not None and isinstance(val, str):
            val = val.upper()
            ret = val.replace("-", "_")
            self._scm_override_key = ret
        else:  # pragma: no cover
            pass

    @property
    def scm_val(self):
        """setuptools-scm value.

        :returns: setuptools-scm val for forcing a particular version
        :rtype: str
        """
        return self._scm_override_val

    @property
    def pkg_name(self):
        """Package name from pyproject.toml project.name

        :returns: Package name
        :rtype: str
        """
        return self._pkg_name

    @property
    def version_file(self):
        """Version file relative path.

        :returns: version file relative path
        :rtype: str | None
        """
        return self._version_file

    @version_file.setter
    def version_file(self, val) -> None:
        """Version file setter.

        :param val: relative Path to version file
        :type val: typing.Any | None
        :raises:

           - :py:exc:`TypeError` -- expecting a Path

        """
        if val is None or not isinstance(val, str):
            msg_exc = "Could not get version_file from pyproject.toml"
            raise TypeError(msg_exc)
        else:
            self._version_file = val


def get_tag_version(path):
    """Specifically want version from version file, not current version
    from setuptools-scm and git.

    If ``pyproject.toml`` is missing or malformed raise :py:exc:`AssertionError`.

    For all other issues, issue a warning and fallback to current version.
    Always want a semantic version str, even if it's wrong. The warning will indicate
    what needs to be fixed

    :param path: current working directory path
    :type path: pathlib.Path
    :param is_test: Default False. During testing set to True
    :type is_test: bool | None
    :returns: tag version fall back to current version
    :rtype: str
    :raises:

       - :py:exc:`NotADirectoryError` -- cwd is not a folder

       - :py:exc:`AssertionError` -- pyproject.toml is missing or malformed

       - :py:exc:`ValueError` -- Explicit version str invalid

    """
    kind = "tag"
    try:
        ae = AlterEnv(path, kind)
    except (ValueError, AssertionError):
        raise

    # tag version (from version file) fallback current version
    # catpure warnings and redirect to stderr
    ver = ae.scm_val

    return ver


def write_version_file(path, kind, is_test=False):
    """Writes version file. Uses vendored setuptools-scm code.

    From pyproject.toml requires:

    - project.name

    - tool.pipenv-unlock.version_file

    :param path: current working directory path
    :type path: pathlib.Path
    :param kind:

       version str, "tag", or "current" or "now". For tagged versions, a version str

    :type kind: str
    :param is_test: Default False. During testing set to True
    :type is_test: bool | None
    :raises:

       - :py:exc:`NotADirectoryError` -- cwd is not a folder

       - :py:exc:`AssertionError` -- Could not get package name from pyproject.toml

       - :py:exc:`ValueError` -- Explicit version str invalid

       - :py:exc:`ValueError` -- Only support write to .py or .txt file

    """
    if is_test is None or not isinstance(is_test, bool):
        is_test = False
    else:  # pragma: no cover
        pass

    try:
        ae = AlterEnv(path, kind)
    except (ValueError, AssertionError):
        raise

    ver = ae.scm_val
    root = ae.path_cwd
    if is_test:
        write_to = ae.version_file
        version_file = None
    else:  # pragma: no cover
        write_to = None
        version_file = ae.version_file

    try:
        write_version_files(ver, root, write_to, version_file)
    except ValueError:
        # if is_test=True does not validate the template, so ValueError
        # target not a ``.txt`` or ``.py`` file
        raise


def build_package(path, kind):
    """Build package.

    Replaces / obsoletes

    .. code-block:: shell

       python igor.py build_next "0.0.1"
       python igor.py build_next "tag"
       python igor.py build_next "current"
       python igor.py build_next "now"

    :param path: Current working directory path
    :type path: pathlib.Path
    :param kind:

       version str, "tag", or "current" or "now". For tagged versions, a version str

    :type kind: str
    :returns: True if build succeeded otherwise False
    :rtype: bool
    :raises:

       - :py:exc:`NotADirectoryError` -- cwd is not a folder

       - :py:exc:`AssertionError` -- Could not get package name from git

       - :py:exc:`ValueError` -- Explicit version str invalid

    .. caution:: side effect

       kind will update [app name]/src/_version.py (done by setupttools-scm)

    """
    # expecting Path cwd
    try:
        ae = AlterEnv(path, kind)
    except Exception:
        raise
    env = ae.modify_env()

    # get lock state --> send to backend
    # 0 to lock; 1 to unlock
    # --config-setting="--set-lock=1"
    cmd = [sys.executable, "-m", "build"]
    t_out = run_cmd(cmd, cwd=ae.path_cwd, env=env)
    out, err, exit_code, str_exception = t_out
    if str_exception is not None:
        """setuptools-scm requires at least one commit. Could not get
        semantic version"""
        print(str_exception, file=sys.stderr)
        ret = False
    else:  # pragma: no cover
        is_fail = exit_code != 0
        if is_fail:
            print(out, file=sys.stderr)
            ret = False
        else:
            ret = True

    return ret


def pretag(tag):
    """Idiot check / sanitize proposed tag.

    Validates semantic version str. Printing the fix semantic tag.

    :param tag:

       A semantic version str. Not current tag or now.

    :type tag: str
    :returns: False if an error occurred otherwise True
    :rtype: tuple[bool, str]
    """
    try:
        clean_tag, local = sanitize_tag(tag)
    except ValueError as e:
        msg = str(e)
        bol_ret = False
    else:
        msg = clean_tag
        bol_ret = True

    return bol_ret, msg


def get_current_version(path):
    """Get current version from setuptools-scm.

    :param path: current working directory path
    :type path: pathlib.Path
    :returns:

       package current (semantic) version. None if
       :py:mod:`setuptools-scm <setuptools_scm>` is not installed

    :rtype: str | None
    """
    ret = _current_version(path=path)

    return ret


def _get_branch() -> str:
    """From git, get the current branch name.

    :returns: Branch name
    :rtype: str
    :meta private:
    """
    ret = subprocess.getoutput("git rev-parse --abbrev-ref @")
    return ret


def print_cheats(path, kind):
    """Print cheats.

    :param path: current working directory path
    :type path: pathlib.Path
    :param kind:

       version str, "tag", or "current" or "now". For tagged versions, a version str

    :type kind: str
    :raises:

       - :py:exc:`NotADirectoryError` -- cwd is not a folder

       - :py:exc:`AssertionError` -- Could not get package name from git

       - :py:exc:`ValueError` -- Explicit version str invalid

    """
    REPO_URL = ""
    t_repo_key = ("Source code", "Repository")

    # Initial version these will both fail
    branch = _get_branch()
    sha = subprocess.getoutput("git rev-parse @")

    # expecting Path cwd
    try:
        sv = SemVersion(path=path)
    except (NotADirectoryError, FileNotFoundError) as e:
        raise NotADirectoryError(str(e)) from e

    try:
        # afterwards path available as sv.path_cwd
        ver = sv.version_clean(kind)
    except AssertionError:
        """Could not get package name from git.
        Test: kind="tag", package_name="asdfasfsadfasdfasdf"
        """
        raise
    except ValueError:
        """Explicit version str invalid.
        Test: kind='dog food tastes better than this'"""
        raise

    sv.parse_ver(ver)
    anchor = sv.anchor()

    tp = TomlParser(path)
    d_pyproject_toml = tp.d_pyproject_toml
    if d_pyproject_toml:
        # PROJECT_NAME
        PROJECT_NAME = d_pyproject_toml.get("project", {}).get("name", None)
        # REPO_URL
        d_project_urls = d_pyproject_toml.get("project", {}).get("urls", {})
        for k, v in d_project_urls.items():
            is_repo_key = REPO_URL == "" and k in t_repo_key
            if is_repo_key and isinstance(v, str) and len(v.strip()) != 0:
                REPO_URL = v
    else:  # pragma: no cover
        # If no pyproject.toml or project.name is not set, just abort
        PROJECT_NAME = ""

    is_pyproject_toml = PROJECT_NAME is not None
    if is_pyproject_toml:
        prints = []

        intro_ = f"{PROJECT_NAME} version is {ver}"
        prints.append(intro_)

        egg = f"egg={PROJECT_NAME}==0.0"  # to force a re-install

        rtd_uri = f"https://{PROJECT_NAME}.readthedocs.io"
        changes_page = f"{rtd_uri}/en/{ver}/changes.html#changes-{anchor}"
        prints.append(changes_page)

        gh_commenting = (
            "\n## For GitHub commenting:\n"
            "This is now released as part of "
            f"[{PROJECT_NAME} {ver}]("
            f"https://pypi.org/project/{PROJECT_NAME}/{ver})."
        )
        prints.append(gh_commenting)

        section_run = "\n## To run this code:"
        prints.append(section_run)

        if branch in ("master", "main"):
            msg = f"python3 -m pip install git+{REPO_URL}#{egg}"
            prints.append(msg)
        else:
            msg = f"python3 -m pip install git+{REPO_URL}@{branch}#{egg}"
            prints.append(msg)

        msg = f"python3 -m pip install git+{REPO_URL}@{sha[:20]}#{egg}"
        prints.append(msg)

        msg = (
            "\n## For other collaborators:\n"
            f"git clone {REPO_URL}\n"
            f"cd {PROJECT_NAME}\n"
            f"git checkout {sha}"
        )
        prints.append(msg)

        str_print = "\n".join(prints)
        print(str_print)
    else:  # pragma: no cover
        pass
