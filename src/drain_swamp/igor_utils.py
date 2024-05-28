"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

igor.py utils

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: __all__
   :type: tuple[str, str, str, str]
   :value: ("seed_changelog", "edit_for_release", "build_package", "pretag")

"""

import os
import re
import subprocess
import sys
from pathlib import (
    Path,
    PurePath,
)

from .check_type import is_ok
from .constants import g_app_name
from .package_metadata import PackageMetadata
from .snippet_sphinx_conf import SnipSphinxConf
from .version_semantic import (
    SemVersion,
    SetuptoolsSCMNoTaggedVersionError,
    _current_version,
    _scm_key,
    sanitize_tag,
)

__all__ = (
    "seed_changelog",
    "edit_for_release",
    "build_package",
    "pretag",
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
    """
    path_changelog = path_cwd.joinpath("CHANGES.rst")
    pattern = re.escape(SCRIV_START)
    replacement = f"{UNRELEASED}\n\nNothing yet.\n\n\n" + SCRIV_START
    update_file(
        path_changelog,
        pattern,
        replacement,
    )


def edit_for_release(path_cwd, kind, snippet_co=None):
    """Edit a few files in preparation for a release.

    .. code-block:: text

       [tool.sphinxcontrib-snip]
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
    :returns: None if no error occurred. 1 no doc?/conf.py file. 2 version str was dodgy
    :rtype: int | None
    """
    # user input parsing?
    path_changelog = path_cwd.joinpath("CHANGES.rst")
    path_notice_txt = path_cwd.joinpath("NOTICE.txt")

    try:
        sc = SnipSphinxConf(path=path_cwd)
    except (NotADirectoryError, FileNotFoundError):
        # if no doc?/conf.py ... do nothing
        msg_exc = "As an optimization, doc?/conf.py is needed. It can be an empty file"
        print(msg_exc, file=sys.stderr)
        return 1

    # sc.path_cwd if already filtered
    # ensure app name is not a possible package, so pyproject.toml is loaded
    pm = PackageMetadata(UNRELEASED, path=sc.path_cwd)
    d_pyproject_toml = pm.d_pyproject_toml

    # Get copyright_start_year from pyproject.toml
    d_section = d_pyproject_toml.get("tool", {}).get("sphinxcontrib-snip", {})
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
    except (SetuptoolsSCMNoTaggedVersionError, AssertionError, ValueError) as e:
        msg_exc = str(e)
        print(msg_exc, file=sys.stderr)
        return 2

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


def build_package(path, kind, package_name=None):
    """Build package

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
    :param package_name:

       Default None. project or package name (hyphens or underscores).
       If not provided, will attempt to get from project metadata then pyproject.toml

    :type package_name: str | None
    :returns: True if build succeeded otherwise False
    :rtype: bool
    :raises:

       - :py:exc:`NotADirectoryError` -- cwd is not a folder

       - :py:exc:`AssertionError` -- Could not get package name from git

       - :py:exc:`ValueError` -- Explicit version str invalid

       - :py:exc:`SetuptoolsSCMNoTaggedVersionError` -- Neither a
         tagged version nor a first commit. Create a commit and
         preferrably a tagged version

    .. caution:: side effect

       kind will update [app name]/src/_version.py (done by setupttools-scm)

    """
    # expecting Path cwd
    try:
        sv = SemVersion(path=path)
    except NotADirectoryError:
        raise

    try:
        # afterwards path available as sv.path_cwd
        ver = sv.version_clean(kind, package_name=package_name)
    except AssertionError as e:
        if isinstance(e, SetuptoolsSCMNoTaggedVersionError):
            """For tag and current/now, Neither a tagged version nor a first
            commit. Create a commit and preferrably a tagged version
            Test: use unittest.mock.patch"""
            raise SetuptoolsSCMNoTaggedVersionError(str(e)) from e
        else:
            """Could not get package name from git.
            Test: kind="tag", package_name="asdfasfsadfasdfasdf"
            """
            raise
    except ValueError:
        """Explicit version str invalid.
        Test: kind='dog food tastes better than this'"""
        raise

    scm_override_val = ver
    env = os.environ.copy()
    scm_override_key = _scm_key(g_app_name)
    env |= {scm_override_key: scm_override_val}

    cmd = [sys.executable, "-m", "build"]
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # suppress annoying useless warning
            cwd=sv.path_cwd,
            env=env,
            text=True,
        )
    except subprocess.CalledProcessError as e:  # pragma: no cover
        """setuptools-scm requires at least one commit. Could not get
        semantic version"""
        str_err = str(e)
        print(str_err, file=sys.stderr)
        ret = False
    else:
        str_out = proc.stdout
        is_fail = proc.returncode != 0
        if is_fail:
            str_out = str_out.rstrip()
            print(str_out, file=sys.stderr)
            ret = False
        else:
            ret = True

    return ret


def pretag(tag):
    """Idiot check / sanitize proposed tag

    Validates semantic version str. Printing the fix semantic tag.

    :param tag:

       A semantic version str. Not current tag or now.

    :type tag: str
    :returns: False if an error occurred otherwise True
    :rtype: tuple[bool, str]
    """
    try:
        clean_tag = sanitize_tag(tag)
    except ValueError as e:
        msg = str(e)
        bol_ret = False
    else:
        msg = clean_tag
        bol_ret = True

    return bol_ret, msg


def get_current_version(path):
    """Get current version from setuptools-scm

    :param path: current working directory path
    :type path: pathlib.Path
    :returns:

       package current (semantic) version. None if
       :py:mod:`setuptools-scm <setuptools_scm>` is not installed

    :rtype: str | None
    """
    ret = _current_version(path=path)

    return ret
