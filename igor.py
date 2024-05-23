"""
Functions named do_* are executable from the command line: do_blah is run
by "python igor.py blah".

Versioning should always have:

- at least one tag and
- patch e.g. X.Y.Z, not X.Y

Adapted from

- `https://github.com/nedbat/coveragepy/blob/5124586e92da3e69429002b2266ce41898b953a1/coverage/version.py`_
- `https://raw.githubusercontent.com/nedbat/coveragepy/master/igor.py`_

"""

from __future__ import annotations

import datetime
import inspect
import os
import platform
import pprint
import re
import subprocess
import sys
import types
from pathlib import Path

try:
    from packaging.version import InvalidVersion
    from packaging.version import Version as Version
except ImportError:
    from setuptools.extern.packaging.version import InvalidVersion  # type: ignore
    from setuptools.extern.packaging.version import Version as Version  # type: ignore

REPO_URI = "github.com"
REPO_OWNER = "msftcangoblowm"
g_app_name = "drain_swamp"  # get from packaging, not hardcode
PROJECT_NAME = g_app_name.replace("_", "-")
REPO = f"{REPO_OWNER}/{PROJECT_NAME}"
REPO_URL = f"https://{REPO_URI}/{REPO}"

UNRELEASED = "Unreleased\n----------"
SCRIV_START = ".. scriv-start-here\n\n"
current_alias_default = "current"
current_aliases = (
    "current",
    "now",
)
g_kinds = ("tag", "current", "now")


def sanitize_kind(kind: str | None = None) -> str:
    """Allow kind to be a version str, 'current', 'tag'"""
    if kind is None:
        # Fallback
        kind_ = "tag"
    else:
        if isinstance(kind, str):
            if kind in g_kinds:
                if kind in current_aliases:
                    kind_ = current_alias_default
                else:
                    kind_ = "tag"
            else:
                # Override version str
                kind_ = kind
        else:
            # Fallback
            kind_ = "tag"

    return kind_


def sanitize_tag(ver: str) -> str:
    """Avoid reinventing the wheel, leverage Version
    Removes epoch and local

    ``final`` is not valid

    :raises:

       - :py:exc:`ValueError` -- Invalid token within Version str

    On cli, use with single quote not double quote

    .. code-block:: shell

       python igor.py pretag '1!0.1.1.rc1dev1+g4b33a80.d20240129'

    0.1.1rc1.dev1
    """
    try:
        v = Version(ver)
    except InvalidVersion as e:
        raise ValueError(e) from e

    str_v = str(v)

    # Strip epoch
    try:
        idx = str_v.index("!")
    except ValueError:
        # Contains no epoch
        pass
    else:
        # strip it
        str_v = str_v[idx + 1 :]

    # Strip local
    try:
        idx = str_v.index("+")
    except ValueError:
        # Contains no epoch
        pass
    else:
        str_v = str_v[:idx]

    return str_v


def do_quietly(command: str, cwd: str) -> int:
    """Run a noisy command in a shell to suppress the output"""
    proc = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return proc.returncode


def do_show_env() -> None:
    """Show the environment variables."""
    print("Environment:")
    for env in sorted(os.environ):
        print(f"  {env} = {os.environ[env]!r}")


def print_banner(label: str) -> None:
    """Print the version of Python."""
    try:
        impl = platform.python_implementation()
    except AttributeError:
        impl = "Python"
        PYPY = False
        CPYTHON = False  # noqa: F841
    else:
        PYPY = impl == "PyPy"
        CPYTHON = impl == "CPython"  # noqa: F841
    version = platform.python_version()

    if PYPY:
        version += " (pypy %s)" % ".".join(str(v) for v in sys.pypy_version_info)

    rev = platform.python_revision()
    if rev:
        version += f" (rev {rev})"

    try:
        which_python = os.path.relpath(sys.executable)
    except ValueError:
        # On Windows having a python executable on a different drive
        # than the sources cannot be relative.
        which_python = sys.executable
    print(f"=== {impl} {version} {label} ({which_python}) ===")
    sys.stdout.flush()


def _update_file(fname: str, pattern: str, replacement: str) -> None:
    """Update the contents of a file, replacing pattern with replacement."""
    path_file = Path(fname)
    if path_file.exists():
        with open(fname) as fobj:
            old_text = fobj.read()

        new_text = re.sub(pattern, replacement, old_text, count=1)

        if new_text != old_text:
            print(f"Updating {fname}", file=sys.stderr)
            with open(fname, "w") as fobj:
                fobj.write(new_text)
    else:
        print(f"Cannot update nonexistent file, {fname}", file=sys.stderr)


def get_release_facts(kind: str) -> types.SimpleNamespace:
    """Return an object with facts about the current release.

    Side effect --> Edits _version.py
    """
    facts = types.SimpleNamespace()
    facts.now = datetime.datetime.now()
    # Initial version these will both fail
    facts.branch = subprocess.getoutput("git rev-parse --abbrev-ref @")
    facts.sha = subprocess.getoutput("git rev-parse @")

    # lazy load
    from drain_swamp.version_semantic import (
        SemVersion,
        SetuptoolsSCMNoTaggedVersionError,
    )

    # Don't recommend is_use_final. It's a legacy thing
    # raise NotADirectoryError if path not a folder
    path_cwd = Path.cwd()
    sv = SemVersion(path=path_cwd, is_use_final=True)

    is_app_name_ok = (
        "g_app_name" in globals()
        and g_app_name is not None
        and isinstance(g_app_name, str)
        and len(g_app_name.strip()) != 0
    )
    if is_app_name_ok is True:
        package_name = g_app_name
    else:
        package_name = None

    try:
        clean_ver = sv.version_clean(kind, package_name=package_name)
    except (SetuptoolsSCMNoTaggedVersionError, AssertionError, ValueError):
        facts.ver = None
        facts.shortver = None
        facts.vi = None
        facts.dev = None
        facts.anchor = None
        facts.next_vi = None
    else:
        facts.ver = clean_ver  # w/o final
        sv.parse_ver(clean_ver)
        facts.shortver = sv.version_xyz()
        mjr = sv.major
        mnr = sv.minor
        mcr = sv.micro
        rel = sv.releaselevel
        ser = sv.serial
        facts.vi = (mjr, mnr, mcr, rel, ser)
        facts.dev = sv.dev
        facts.anchor = facts.shortver.replace(".", "-")

        # better to manually edit _version.py
        if rel is not None and isinstance(rel, str) and len(rel) != 0:
            if rel == "final":
                facts.next_vi = (mjr, mnr, mcr + 1, "alpha", 0)
            else:
                # a, b, rc
                facts.anchor += f"{rel[0]}{ser}"
                facts.next_vi = (mjr, mnr, mcr, rel, ser + 1)
        else:
            facts.next_vi = (mjr, mnr, mcr, rel, ser + 1)

    return facts


def do_edit_for_release(kind: str) -> int | None:
    """Edit a few files in preparation for a release.

    Inputs cwd, g_app_name, kind, copyright_start_year
    """
    # lazy load
    from drain_swamp.snippet_sphinx_conf import SnipSphinxConf
    from drain_swamp.version_semantic import SetuptoolsSCMNoTaggedVersionError

    copyright_start_year = "2023"  # pyproject.toml support needed

    # pull from pyproject.toml instead
    is_app_name_ok = (
        "g_app_name" in globals()
        and g_app_name is not None
        and isinstance(g_app_name, str)
        and len(g_app_name.strip()) != 0
    )
    if is_app_name_ok:
        package_name = g_app_name
    else:
        package_name = None

    path_cwd = Path.cwd()
    try:
        sc = SnipSphinxConf(path=path_cwd)
    except (NotADirectoryError, FileNotFoundError):
        # if no doc?/conf.py ... do nothing
        msg_exc = "As an optimization, doc?/conf.py is needed. It can be an empty file"
        print(msg_exc)
        return 1

    # After call, will have sc.SV and sc.author_name_left
    try:
        sc.contents(
            kind,
            package_name,
            copyright_start_year,
        )
    except (SetuptoolsSCMNoTaggedVersionError, AssertionError, ValueError) as e:
        print(str(e))
        return 2

    sc.replace(snippet_co=None)
    author_first_name = sc.author_name_left

    is_dev = sc.SV.dev is not None and isinstance(sc.SV.dev, int)
    if is_dev:
        print(f"**\n** This is a dev release: {sc.SV.__version__}\n**\n\nNo edits")
        return

    # NOTICE.txt
    regex_pattern = r"Copyright {0}.*? {1}".format(
        copyright_start_year,
        author_first_name,
    )
    str_year_end = sc.now_to_str("%Y")
    str_dt_ymd = sc.now_to_str("%Y-%m-%d")

    replace_with = f"Copyright {0}-{1} {author_first_name}".format(
        copyright_start_year,
        str_year_end,
        author_first_name,
    )
    _update_file("NOTICE.txt", regex_pattern, replace_with)

    # CHANGES.rst
    ver = sc.__version__
    anchor = sc.anchor()
    if ver is not None and anchor is not None:
        title = f"Version {ver} — {str_dt_ymd}"
        rule = "-" * len(title)
        new_head = f".. _changes_{anchor}:\n\n{title}\n{rule}"

        _update_file("CHANGES.rst", re.escape(SCRIV_START), "")
        _update_file("CHANGES.rst", re.escape(UNRELEASED), SCRIV_START + new_head)


def do_bump_version(kind: str) -> None:
    """Edit a few files right after a release to bump the version."""

    # CHANGES.rst
    _update_file(
        "CHANGES.rst",
        re.escape(SCRIV_START),
        f"{UNRELEASED}\n\nNothing yet.\n\n\n" + SCRIV_START,
    )

    """
    kind_: str = sanitize_kind(kind)
    facts = get_release_facts(kind_)  # noqa: F841
    file_path = f"src/{g_app_name}/constants.py"
    next_version = f"version_info = {facts.next_vi}\n_dev = 1".replace("'", '"')
    _update_file(
        file_path,
        r"(?m)^version_info = .*\n_dev = \d+$",
        next_version,
    )
    """
    pass


def do_cheats(kind: str):
    """Show a cheatsheet of useful things during releasing."""
    kind_: str = sanitize_kind(kind)
    facts = get_release_facts(kind_)
    pprint.pprint(facts.__dict__)
    print(f"\n{PROJECT_NAME} version is {facts.ver}")

    egg = f"egg={PROJECT_NAME}==0.0"  # to force a re-install
    print(
        f"https://{PROJECT_NAME}.readthedocs.io/en/{facts.ver}/changes.html#changes-{facts.anchor}"
    )

    print(
        "\n## For GitHub commenting:\n"
        + "This is now released as part of "
        + f"[{g_app_name} {facts.ver}](https://pypi.org/project/{PROJECT_NAME}/{facts.ver})."
    )

    print("\n## To run this code:")
    if facts.branch in ("master", "main"):
        print(f"python3 -m pip install git+{REPO_URL}#{egg}")
    else:
        print(f"python3 -m pip install git+{REPO_URL}@{facts.branch}#{egg}")
    print(f"python3 -m pip install git+{REPO_URL}@{facts.sha[:20]}#{egg}")

    print(
        "\n## For other collaborators:\n"
        + f"git clone {REPO_URL}\n"
        + f"cd {PROJECT_NAME}\n"
        + f"git checkout {facts.sha}"
    )


def do_help() -> None:
    """List the available commands"""
    items = list(globals().items())
    items.sort()
    for name, value in items:
        if name.startswith("do_"):
            print(f"{name[3:]:<20}{value.__doc__}")


def current_tag() -> str | None:
    """Run git describe --tag"""
    cmd = ["/bin/git", "describe", "--tag"]
    path_cwd = Path.cwd()
    proc = subprocess.run(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=str(path_cwd),
        text=True,
    )

    str_out = None
    if isinstance(proc, subprocess.CompletedProcess):
        str_out = proc.stdout
        str_out = str_out.rstrip()

    return str_out


def scm_key(prog_name: str) -> str:
    # hyphen --> underscore. Uppercase
    G_APP_NAME = prog_name.upper()

    scm_override_key = f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{G_APP_NAME}"

    return scm_override_key


def _current_version() -> str | None:
    path_cwd = Path.cwd()
    cmd = [sys.executable, "setup.py", "--version"]
    proc = subprocess.run(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # suppress annoying useless warning
        cwd=str(path_cwd),
        text=True,
    )
    str_out = None
    if isinstance(proc, subprocess.CompletedProcess):
        str_out = proc.stdout
        str_out = str_out.rstrip()

    return str_out


def do_current_version() -> None:
    """Does not communicate with setuptools_scm / setuptools so version
    is same as shown by git

    Writes the version file, ``src/[package]/_version.py``
    If not in dev mode, will also have to copy this into same file in the venv
    """
    str_out = _current_version()

    if str_out is not None:
        print(str_out)


def _arbritary_version(next_version: str) -> str | None:
    path_cwd = Path.cwd()
    cwd_path = str(path_cwd)
    scm_override_key = scm_key(g_app_name)

    if next_version is None or (
        next_version is not None
        and isinstance(next_version, str)
        and len(next_version) == 0
    ):
        scm_override_val = current_tag()
    else:
        scm_override_val = next_version

    # Get tagged version number from setup.py
    env = os.environ.copy()
    # https://peps.python.org/pep-0584/
    env |= {scm_override_key: scm_override_val}

    cmd = [sys.executable, "setup.py", "--version"]
    proc = subprocess.run(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # suppress annoying useless warning
        cwd=cwd_path,
        env=env,
        text=True,
    )
    str_out = None
    if isinstance(proc, subprocess.CompletedProcess):
        str_out = proc.stdout
        str_out = str_out.rstrip()

    return str_out


def _tag_version(next_version: str | None = "") -> str | None:
    """Get version potentially overriding it"""
    # empty str means take current tag version
    ret = _arbritary_version(next_version)

    return ret


def do_tag_version() -> None:
    """From setup.py, get latest tagged version

    Writes the version file, ``src/[package]/_version.py``
    If not in dev mode, will also have to copy this into same file in the venv

    Equivalent command

    .. code-block:: shell

        SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ASZ="$(git describe --tag)" python \
        setup.py --version 2>/dev/null

    Duration (real): 0m0.801s
    """
    str_out = _tag_version()

    if str_out is not None:
        print(str_out)


def do_version(kind: str) -> None:
    """Updates version based on kind: ``current`` or ``tag``"""
    kind_: str = sanitize_kind(kind)
    if kind is not None and kind in g_kinds:
        func = _current_version if kind_ == current_alias_default else _tag_version
        print(func())
    else:
        print(kind)


def do_build_next(next_version: str) -> None:
    """build, the current checked out as, current tagged version

    Current tag: :code:`git describe --tag`

    To build a previous build
    --------------------------

    `Tagging basics <https://git-scm.com/book/en/v2/Git-Basics-Tagging>`_

    `man git-tag <https://git-scm.com/docs/git-tag#_discussion>`_

    Create a new tag at commit, ``1b2b3b4``. Then advertise the tag

    .. code-block:: shell

       git tag -as -m 'blah blah' 0.1.0 1b2b3b4
       git push origin 0.1.0
       git push origin --tags

    When detaching from HEAD, checking out a previous commit, hopefully
    into a different branch, tag the commit

    Equivalent command -- no tagged versions exist

    .. code-block: shell

       SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="0.0.1" python -m build
       python igor.py build_next "0.0.1"

    Equivalent command -- tagged versions exist

    .. code-block: shell

       PYTHONWARNINGS="ignore" SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DRAIN_SWAMP="$(git describe --tag)" python -m build

    Check -- has tagged release. If not --> exit code 128

    .. code-block:: shell

       git log --decorate=full

    If no tagged releases will return exit code 128

    Do not do these commands. Will overwrite _version.py with a development release

    .. code-block: shell

       python setup.py --version 2>/dev/null
       python -m build

    """
    path_cwd = Path.cwd()
    cwd_path = str(path_cwd)
    env = os.environ.copy()

    if next_version is None or (
        next_version is not None
        and isinstance(next_version, str)
        and len(next_version.strip()) == 0
    ):
        msg = "Use current version, not tagged or provided version"
        print(msg)
    else:
        # Updates src/[prog name]/_version.py with bumped version
        scm_override_val = _arbritary_version(next_version)
        # https://peps.python.org/pep-0584/
        scm_override_key = scm_key(g_app_name)
        env |= {scm_override_key: scm_override_val}

    cmd = [sys.executable, "-m", "build"]

    # Build bumped version, eventhough not tagged yet
    proc = subprocess.run(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 2>&1
        cwd=cwd_path,
        env=env,
        text=True,
    )
    if isinstance(proc, subprocess.CompletedProcess):
        str_out = proc.stdout
        str_out = str_out.rstrip()
        print(str_out)
        ret = 0
    else:
        ret = 1

    return ret


def do_pretag(tag: str) -> int:
    """Idiot check / sanitize proposed tag"""
    try:
        clean_tag = sanitize_tag(tag)
    except ValueError as e:
        print(e)
        ret = 1
    else:
        print(clean_tag)
        ret = 0

    return ret


def _analyze_args(function: types.FunctionType) -> tuple[bool, int]:
    """What kind of args does `function` expect?

    :param function: module level function. Inspect arg spec
    :type function: types.FunctionType
    :returns:

       - star -- Does `function` accept *args?
       - num_args -- How many positional arguments does `function` have?

    :rtype: tuple[bool, int]
    """
    argspec = inspect.getfullargspec(function)
    return bool(argspec.varargs), len(argspec.args)


def main(args: list[str]) -> int:
    """Main command-line execution for igor.

    Verbs are taken from the command line, and extra words taken as directed
    by the arguments needed by the handler.

    :returns:

       - 1 -- No handler for verb
       - n -- Failure exit code

    :rtype: int
    """
    while args:
        verb = args.pop(0)
        handler = globals().get("do_" + verb)
        if handler is None:
            print(f"*** No handler for {verb!r}")
            return 1

        star, num_args = _analyze_args(handler)
        if star:
            # Handler has *args, give it all the rest of the command line.
            handler_args = args
            args = []
        else:
            # Handler has specific arguments, give it only what it needs.
            handler_args = args[:num_args]
            args = args[num_args:]

        ret = handler(*handler_args)
        # If a handler returns a failure-like value, stop.
        if ret:
            return ret

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
