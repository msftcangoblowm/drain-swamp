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

# pep366 ...
# https://stackoverflow.com/a/34155199
if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    # Package not installed
    # python src/drain_swamp/cli_igor.py build --kind="0.0.1"
    path_d = Path(__file__).parent
    rev_mods = []
    while path_d.joinpath("__init__.py").exists():
        name = path_d.name
        path_d = path_d.parent
        rev_mods.append(name)
    tmp_pkg = ".".join(reversed(rev_mods))
    sys.path.insert(1, str(path_d))
    mod = __import__(tmp_pkg)
    sys.modules[tmp_pkg] = mod
    __package__ = tmp_pkg
elif (
    __name__ == "__main__" and isinstance(__package__, str) and len(__package__) == 0
):  # pragma: no cover
    # Package installed
    # python -m drain_swamp.cli_igor build --kind="0.0.1"
    tmp_pkg = "drain_swamp"
    path_pkg_base_dir = Path(__file__).parent.parent
    sys.path.insert(1, str(path_pkg_base_dir))
    mod = __import__(tmp_pkg)
    sys.modules[tmp_pkg] = mod
    __package__ = tmp_pkg
else:
    # normal import
    __package__ = "drain_swamp"
# pep366 ...done

from .constants import (
    __version_app,
    g_app_name,
)
from .igor_utils import (
    build_package,
    edit_for_release,
    get_current_version,
    pretag,
    seed_changelog,
)
from .version_semantic import SetuptoolsSCMNoTaggedVersionError

_logger = logging.getLogger(f"{g_app_name}.cli_igor")
# taken from pyproject.toml
entrypoint_name = "igor"  # noqa: F401

help_path = "package root folder"
help_snippet_co = (
    "Snippet code, within a file, unique id of an editable region, aka snippet. "
    "Only necessary if allows for multiple snippets"
)
help_kind = (
    "version string kind: now (alias of current), current, tag, or "
    "explicit semantic version"
)
help_package_name = (
    "Setuptools-scm environment variable contains the package name. "
    """When --kind is "tag", and not provided, queries git. Better to avoid"""
)

EPILOG_SEED = """
EXIT CODES

0 -- always

"""

EPILOG_EDITS = """
EXIT CODES

0 -- Evidently sufficient effort put into unittesting. Job well done, beer on me!

1 -- no doc?/conf.py folder or file

2 -- semantic version str is malformed

"""

EPILOG_BUILD = """
EXIT CODES

0 -- Package built and placed in dist/

1 -- Package build failed. Should print entire build output

2 -- Expecting current working folder to be project base folder. Not a folder

4 -- Could not get package name from git, needed to set the correct version

5 -- Not valid a semantic version str. Only occurs when a version str is provided

6 -- When getting tag or current version, no commits nor tagged releases

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


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version_app)
def main():
    """Command-line for igor. Prints usage"""


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
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help=help_path,
)
def seed(path):
    """If file [path]/CHANGES.rst does not exist, a warning is logged,
    need to capture that log entry

    \f
    :param path: path to the current working directory containing pyproject.toml
    :type path: pathlib.Path
    """
    with contextlib.redirect_stderr(io.StringIO()) as f_stream:
        seed_changelog(path)
    str_err = f_stream.getvalue()
    click.echo(str_err)


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
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
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
    with contextlib.redirect_stderr(io.StringIO()) as f_stream:
        opt_int = edit_for_release(path, kind, snippet_co=snippet_co)
    str_err = f_stream.getvalue()
    click.echo(str_err)

    if opt_int is None:
        sys.exit(0)
    else:
        sys.exit(opt_int)


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
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
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
    "-n",
    "--package-name",
    "package_name",
    type=click.STRING,
    default=None,
    help=help_package_name,
)
def semantic_version_aware_build(path, kind, package_name):
    try:
        with contextlib.redirect_stderr(io.StringIO()) as f_stream:
            # click --> exit code 2. Preventing NotADirectoryError
            bol_out = build_package(path, kind, package_name=package_name)
    except AssertionError as e:
        if isinstance(e, SetuptoolsSCMNoTaggedVersionError):
            msg_exc = str(e)
            click.echo(msg_exc)
            sys.exit(6)
        else:
            # AssertionError
            msg_exc = str(e)
            click.echo(msg_exc)
            sys.exit(4)
    except ValueError as e:
        msg_exc = str(e)
        click.echo(msg_exc)
        sys.exit(5)
    if not bol_out:
        # need entire output to know how to deal with the failure
        str_err = f_stream.getvalue()
        click.echo(str_err)
        sys.exit(1)
    else:
        sys.exit(0)


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
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help=help_path,
)
def current_version(path):
    """Usage

    python src/drain_swamp/cli_igor.py current

    \f
    :param path: current working directory
    :type path: pathlib.Path
    """
    opt_str = get_current_version(path)
    if opt_str is None:
        sys.exit(1)
    else:
        click.echo(opt_str)
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
