"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

**Update changelog, NOTICE.txt and ``docs?/conf.py``**

.. code-block:: shell

   igor seed
   igor edits

1. Writes a placeholder block to CHANGES.rst
2. Edits:

   - doc?/conf.py
   - NOTICE.txt
   - CHANGES.rst

**Build package**

Running these commands will also update src/[package name]/_version.py

.. code-block:: shell

   python src/drain_swamp/cli_igor.py build --kind="0.0.1"

or

.. code-block:: shell

   python -m drain_swamp.cli_igor build --kind="0.0.1"

First first form can be run from source, without the package being installed

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: help_path
   :type: str

   cli option ``--path`` doc string

.. py:data:: help_kind
   :type: str

   cli option ``--kind`` doc string

.. py:data:: help_snippet_co
   :type: str

   cli option --snip doc string

.. py:data:: EPILOG_SEED
   :type: str

   Exit codes explanation for command, ``seed``

.. py:data:: EPILOG_EDITS
   :type: str

   Exit codes explanation for command, ``edits``

.. py:data:: EPILOG_BUILD
   :type: str

   Exit codes explanation for command, ``build``

.. py:data:: EPILOG_PRETAG
   :type: str

   Exit codes explanation for command, ``pretag``

"""

import contextlib
import io
import logging
import sys
from pathlib import Path

import click
from drain_swamp_snippet import (
    ReplaceResult,
    Snip,
)

# pep366 ...
# https://stackoverflow.com/a/34155199
if __name__ == "__main__" and __spec__ is None:  # pragma: no cover
    # Package not installed
    # python src/drain_swamp/cli_igor.py build --kind="0.0.1"
    import importlib.util

    path_d = Path(__file__).parent
    rev_mods = []
    while path_d.joinpath("__init__.py").exists():
        name = path_d.name
        path_prev = path_d
        path_d = path_d.parent
        rev_mods.append(name)
    # One level above top package --> sys.path.insert
    sys.path.insert(1, str(path_d))
    # parent (aka package) dotted path
    dotted_path = ".".join(reversed(rev_mods))

    # print(f"str(path_d): {str(path_d)}", file=sys.stderr)
    # print(f"dotted_path: {dotted_path}", file=sys.stderr)
    # print(f"path_prev: {path_prev}", file=sys.stderr)
    pass

    # import top package level
    path_top = path_prev.joinpath("__init__.py")
    spec_top = importlib.util.spec_from_file_location(name, path_top)
    mod_top = importlib.util.module_from_spec(spec_top)
    sys.modules[dotted_path] = mod_top
    spec_top.loader.exec_module(mod_top)

    # __spec__ is None. Set __spec__ rather than :code:`__package__ = dotted_path`
    dotted_path_this = f"{dotted_path}.{Path(__file__).stem}"
    spec_this = importlib.util.spec_from_file_location(dotted_path_this, Path(__file__))
    __spec__ = spec_this
elif (
    __name__ == "__main__" and isinstance(__package__, str) and len(__package__) == 0
):  # pragma: no cover
    # When package is not installed
    # python -m drain_swamp.cli_igor build --kind="0.0.1"
    tmp_pkg = "drain_swamp"
    path_pkg_base_dir = Path(__file__).parent.parent
    sys.path.insert(1, str(path_pkg_base_dir))
    mod = __import__(tmp_pkg)
    sys.modules[tmp_pkg] = mod
    __package__ = tmp_pkg
else:
    # normal import
    # __package__ = "drain_swamp"
    pass
# pep366 ...done

from .constants import g_app_name
from .igor_utils import (
    build_package,
    edit_for_release,
    get_current_version,
    get_tag_version,
    pretag,
    print_cheats,
    seed_changelog,
    write_version_file,
)
from .snippet_sphinx_conf import SnipSphinxConf

_logger = logging.getLogger(f"{g_app_name}.cli_igor")
# taken from pyproject.toml
entrypoint_name = "drain-swamp"  # noqa: F401

help_path = "package root folder"
help_snippet_co = (
    "Snippet code, within a file, unique id of an editable region, aka snippet. "
    "Only necessary if allows for multiple snippets"
)
help_kind = (
    "version string kind: now (alias of current), current, tag, or "
    "explicit semantic version"
)

EPILOG_SEED = """
EXIT CODES

0 -- always
1 -- missing start token
2 -- file not found or permissions issue

"""

EPILOG_EDITS = """
EXIT CODES

0 -- Evidently sufficient effort put into unittesting. Job well done, beer on me!

1 -- no doc?/conf.py folder or file

2 -- semantic version str is malformed

"""

EPILOG_LIST = """
EXIT CODES

0 -- Printed snippet codes list and list of snippet code with respective block

3 -- Expected a doc/ or docs/ folder

4 -- Expected to find file, doc/conf.py or docs/conf.py

5 -- Snippet validation fail. Either nested or non-matching start/end tokens

6 -- There are no snippets

"""

EPILOG_BUILD = """
EXIT CODES

0 -- Package built and placed in dist/

1 -- Package build failed. Should print entire build output

2 -- Expecting current working folder to be project base folder. Not a folder

4 -- Could not get package name from pyproject.toml, needed to set the correct version

5 -- Not valid a semantic version str. Only occurs when a version str is provided

"""

EPILOG_SCM_PAIR = """

0 -- Package built and placed in dist/

2 -- Expecting current working folder to be project base folder. Not a folder

4 -- Could not get package name from pyproject.toml, needed to set the correct version

5 -- Not valid a semantic version str. Only occurs when a version str is provided

"""

EPILOG_PRETAG = """
EXIT CODES

0 -- Sanitized semantic version str

1 -- Error with semantic version str. Cannot be fixed

"""

EPILOG_CURRENT_VERSION = """

0 -- Current semantic version str

1 -- Most likely setuptools-scm package is not installed otherwise command failed

"""

EPILOG_TAG_VERSION = """

0 -- Tag semantic version str from version file or fallback current version

1 -- Most likely setuptools-scm package is not installed otherwise command failed

4 -- --kind nonsense. Explicit version str invalid

6 -- Could not get package name from git

"""

EPILOG_CHEATS = """

0 -- printed the cheats

2 -- Unknown parameter or parameter has unsupported type

3 -- Expecting a folder, got something else

4 -- --kind nonsense. Explicit version str invalid

6 -- Could not get package name from git

"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
def main():
    """Command-line for drain-swamp. Prints usage"""


@main.command(
    "seed",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_SEED,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
def seed(path):
    """Updates changelog, ``CHANGES.rst``, creating placeholder

    If file [path]/CHANGES.rst does not exist, a warning is logged,
    need to capture that log entry

    \f
    :param path: path to the current working directory containing pyproject.toml
    :type path: pathlib.Path
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    f_stream = io.StringIO()
    with contextlib.redirect_stderr(f_stream):
        exit_code = seed_changelog(path)
    str_err = f_stream.getvalue()

    # always a msg printed onto strerr
    click.echo(str_err, err=True)

    is_exit_code = exit_code != 0
    if is_exit_code:
        sys.exit(exit_code)
    else:  # pragma: no cover
        pass


@main.command(
    "edits",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_EDITS,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
@click.option(
    "-k",
    "--kind",
    "kind",
    default="tag",
    type=click.STRING,
    help=help_kind,
)
@click.option(
    "-s",
    "--snip",
    "snippet_co",
    default=None,
    type=click.STRING,
    help=help_snippet_co,
)
def edit(path, kind, snippet_co=None):  # pragma: no cover
    """Edits: doc?/conf.py, NOTICE.txt, and CHANGES.rst

    \f
    :param path: path to the current working directory containing pyproject.toml
    :type path: pathlib.Path
    :param kind:

       semantic version str or "current" or "now" or "tag". Side effect
       changes ``src/[app name]/_version.py``

    :type kind: str
    :param snippet_co: Sphinx doc?/conf.py snippet code. Supply none is no snippet has no code
    :type snippet_co: str | None
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    with contextlib.redirect_stderr(io.StringIO()) as f_stream:
        opt_int = edit_for_release(path, kind, snippet_co=snippet_co)
    str_err = f_stream.getvalue()
    click.echo(str_err, err=True)

    if opt_int is None:
        sys.exit(0)
    else:
        sys.exit(opt_int)


@main.command(
    "list",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_LIST,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
def snippets_list(path):
    """In Sphinx doc?/conf.py, list snippets

    path is the package base folder. Searches for ``doc?/conf.py``

    .. code-block shell:

       drain-swamp list
       cd tests
       drain-swamp list --path=..

    \f
    :param path:

       Default current working directory. package root folder. Must
       contain ``pyproject.toml``

    :type path: pathlib.Path
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    # Get absolute path to doc?/conf.py
    try:
        sc = SnipSphinxConf(path=path)
    except NotADirectoryError:
        msg_exc = "Expected a doc/ or docs/ folder"
        click.secho(msg_exc, fg="red", err=True)
        sys.exit(3)
    except FileNotFoundError:
        msg_exc = "Expected to find file, doc/conf.py or docs/conf.py"
        click.secho(msg_exc, fg="red", err=True)
        sys.exit(4)

    abspath_conf_py = sc.path_abs

    # print:
    # - snippet codes
    # - snippets
    snip = Snip(abspath_conf_py)
    with contextlib.redirect_stderr(io.StringIO()) as f:
        snippets = snip.print()
    msg = f.getvalue()
    if isinstance(snippets, ReplaceResult):
        click.secho(msg, fg="red", err=True)
        if snippets == ReplaceResult.VALIDATE_FAIL:
            sys.exit(5)
        elif snippets == ReplaceResult.NO_MATCH:
            sys.exit(6)
        else:  # pragma: no cover
            pass
    else:
        click.secho(msg, fg="green", err=True)


@main.command(
    "build",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_BUILD,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
@click.option(
    "-k",
    "--kind",
    "kind",
    default="tag",
    type=click.STRING,
    help=help_kind,
)
def semantic_version_aware_build(path, kind):
    """Build package

    \f
    :param path: current working directory
    :type path: pathlib.Path
    :param kind:

       semantic version str or "current" or "now" or "tag". Side effect
       changes ``src/[app name]/_version.py``

    :type kind: str
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    try:
        with contextlib.redirect_stderr(io.StringIO()) as f_stream:
            # click --> exit code 2. Preventing NotADirectoryError
            bol_out = build_package(path, kind)
    except AssertionError as e:
        # AssertionError
        msg_exc = str(e)
        click.echo(msg_exc, err=True)
        sys.exit(4)
    except ValueError as e:
        msg_exc = str(e)
        click.echo(msg_exc, err=True)
        sys.exit(5)
    if not bol_out:
        # need entire output to know how to deal with the failure
        str_err = f_stream.getvalue()
        click.echo(str_err, err=True)
        sys.exit(1)
    else:
        sys.exit(0)


@main.command(
    "write_version",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_SCM_PAIR,
    deprecated=True,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
@click.option(
    "-k",
    "--kind",
    "kind",
    default="tag",
    type=click.STRING,
    help=help_kind,
)
def setuptools_scm_key_value_pair(path, kind):
    """Given kind, write version str to version_file

    \f
    :param path: current working directory
    :type path: pathlib.Path
    :param kind:

       semantic version str or "current" or "now" or "tag". Side effect
       changes ``src/[app name]/_version.py``

    :type kind: str

    .. deprecated:: 0.5.1

       Version file written by plugin, ds_scm_version, during sdist
       build. Might remain relevent only to initially create the version file

    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    try:
        with contextlib.redirect_stderr(io.StringIO()):
            # click --> exit code 2. Preventing NotADirectoryError
            write_version_file(path, kind)
    except AssertionError as e:
        # AssertionError
        msg_exc = str(e)
        click.echo(msg_exc, err=True)
        sys.exit(4)
    except ValueError as e:
        msg_exc = str(e)
        click.echo(msg_exc, err=True)
        sys.exit(5)


@main.command(
    "pretag",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_PRETAG,
)
@click.argument("ver", type=click.STRING)
def validate_tag(ver):
    """Print the sanitized semantic version str

    Normal cli usage

    drain-swamp pretag "0.0.1"

    Usage when package is not installed

    python src/drain_swamp/cli_igor.py pretag "0.0.1"

    Usage if package is installed

    python -m drain_swamp.cli_igor pretag "0.0.1"

    \f
    :param ver: Possibility malformed semantic ver str
    :type ver: str
    """
    is_success, sanitized = pretag(ver)
    click.echo(sanitized)
    if is_success:
        sys.exit(0)
    else:
        sys.exit(1)


@main.command(
    "current",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_CURRENT_VERSION,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
def current_version(path):
    """Get scm version str

    python src/drain_swamp/cli_igor.py current

    or

    drain-swamp current

    \f
    :param path: current working directory
    :type path: pathlib.Path
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    opt_str = get_current_version(path)
    if opt_str is None:
        sys.exit(1)
    else:
        click.echo(opt_str)
        sys.exit(0)


@main.command(
    "tag",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_TAG_VERSION,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
def tag_version(path):
    """Get semantic version str from version_file. Fall back to current version

    python src/drain_swamp/cli_igor.py tag

    or

    drain-swamp tag

    \f
    :param path: current working directory
    :type path: pathlib.Path
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    # NotADirectoryError prevents by click
    try:
        ver_sem = get_tag_version(path)
    except ValueError as e:
        """tag version skipped if version file semantic version str is
        invalid. Then if current version is invalid --> ValueError"""
        msg = str(e)
        exit_code = 4
    except AssertionError as e:
        # pyproject.toml file missing or malformed
        msg = str(e)
        exit_code = 6
    else:
        msg = None
        exit_code = 0

    if msg is not None:
        click.secho(msg, fg="green", err=True)
        sys.exit(exit_code)
    else:  # pragma: no cover
        click.echo(ver_sem)


@main.command(
    "cheats",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_CHEATS,
)
@click.option(
    "-p",
    "--path",
    "path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=True, dir_okay=True, resolve_path=True),
    help=help_path,
)
@click.option(
    "-k",
    "--kind",
    "kind",
    default="tag",
    type=click.STRING,
    help=help_kind,
)
def do_cheats(path, kind):
    """Get useful notes to aid in kitting and publishing

    python src/drain_swamp/cli_igor.py cheats

    or

    drain-swamp cheats

    \f
    :param path: current working directory
    :type path: pathlib.Path
    :param kind:

       semantic version str or "current" or "now" or "tag". Side effect
       changes ``src/[app name]/_version.py``

    :type kind: str
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path = Path(path)
    else:  # pragma: no cover
        pass

    try:
        print_cheats(path, kind)
    except NotADirectoryError as e:
        # Expecting a folder, got something else
        msg = str(e)
        exit_code = 3
    except ValueError as e:
        # --kind nonsense. Explicit version str invalid
        msg = str(e)
        exit_code = 4
    except AssertionError as e:
        # Could not get package name from git
        msg = str(e)
        exit_code = 6
    else:
        msg = None
        exit_code = 0

    if msg is not None:
        click.secho(msg, fg="green", err=True)
    else:  # pragma: no cover
        pass

    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
