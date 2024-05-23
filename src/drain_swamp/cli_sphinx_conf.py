"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

sphinxcontrib-snip entrypoint

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

.. py:data:: help_path
   :type: str

   cli option ``--path`` doc string

.. py:data:: help_kind
   :type: str

   cli option ``--kind`` doc string

.. py:data:: help_copyright_year
   :type: str

   cli option ``--start-year`` doc string

.. py:data:: help_snippet_co
   :type: str

   cli option ``--snip`` doc string

.. py:data:: EPILOG
   :type: str

   Text block following entrypoint description. Explains meaning of each exit code

"""

import logging
import sys
import traceback
from pathlib import Path

import click

# pep366 ...
# https://stackoverflow.com/a/34155199
if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    # Package not installed
    # python src/drain_swamp/cli_sphinx_conf.py snip --snip=little_shop_of_horrors_shrine_candles
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
elif (
    __name__ == "__main__" and isinstance(__package__, str) and len(__package__) == 0
):  # pragma: no cover
    # Package installed
    # python -m drain_swamp.cli_sphinx_conf snip --snip=little_shop_of_horrors_shrine_candles
    tmp_pkg = "drain_swamp"
    path_pkg_base_dir = Path(__file__).parent.parent
    sys.path.insert(1, str(path_pkg_base_dir))
    mod = __import__(tmp_pkg)
    sys.modules[tmp_pkg] = mod
    __package__ = tmp_pkg
else:
    # sphinxcontrib-snip snip --snip=little_shop_of_horrors_shrine_candles
    __package__ = "drain_swamp"
# pep366 ...done

from .constants import (
    __version_app,
    g_app_name,
)
from .exceptions import PyProjectTOMLParseError
from .parser_in import get_pyproject_toml
from .snippet_sphinx_conf import SnipSphinxConf

_logger = logging.getLogger(f"{g_app_name}.cli_sphinx_conf")
# taken from pyproject.toml
entrypoint_name = "sphinxcontrib-snip"  # noqa: F401

help_path = "package root folder"

help_kind = (
    "version string kind: now (is alias of current), current, tag, or "
    "explicit semantic version"
)

help_copyright_year = "copyright start year. Provide as an int"

help_snippet_co = (
    "Snippet code, within a file, unique id of an editable region, aka snippet. "
    "Only necessary if allows for multiple snippets"
)

EPILOG = """
EXIT CODES

0 -- Evidently sufficient effort put into unittesting. Job well done, beer on me!

1 -- No replace occurred. Does snippet_co match the code in the [doc folder]/conf.py snippet?

3 -- Expected a doc/ or docs/ folder. No such folder

4 -- Expected to find file, doc/conf.py or docs/conf.py

5 -- pyproject.toml either does not exist or validation fail

6 -- From pyproject.toml, could not get package name

"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version_app)
def main():
    """Command-line for sphinxcontrib-snip. Prints usage"""


@main.command(
    "snip",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help=help_path,
)
@click.option(
    "-k",
    "--kind",
    "kind",
    default="current",
    type=click.STRING,
    help=help_kind,
)
@click.option(
    "-y",
    "--start-year",
    "copyright_start_year",
    default=1970,
    type=click.INT,
    help=help_copyright_year,
)
@click.option(
    "-s",
    "--snip",
    "snippet_co",
    default=None,
    type=click.STRING,
    help=help_snippet_co,
)
def sphinx_conf_snip(path, kind, copyright_start_year, snippet_co):
    """From package root folder, Sphinx folder is usually in ``doc/``
    or ``docs/``. Either one is fine.

    Sphinx configuration file would be ``[doc folder]/conf.py``

    Within the Sphinx ``conf.py``, there should be one or more editable
    snippets. For example,

    Without a snippet code. Which is ok if only one snippet / file

    .. code-block:: text

       # @@@ editable
       copyright = "2023–2024, Dave Faulkmore"
       # The short X.Y.Z version.
       version = "0.0.1"
       # The full version, including alpha/beta/rc tags.
       release = "0.0.1"
       # The date of release, in "monthname day, year" format.
       release_date = "April 25, 2024"
       # @@@ end

    or with a snippet code. So can have many snippets / file

    .. code-block:: text

       # @@@ editable i_am_snippet_co
       copyright = "2023–2024, Dave Faulkmore"
       # The short X.Y.Z version.
       version = "0.0.1"
       # The full version, including alpha/beta/rc tags.
       release = "0.0.1"
       # The date of release, in "monthname day, year" format.
       release_date = "April 25, 2024"
       # @@@ end

    In a file, if same content is required in multiple places, reuse the snippet code.

    Have fun. It's dummy proof.

    \f
    :param path:

       Default current working directory. package root folder. Must
       contain ``pyproject.toml``

    :type path: pathlib.Path
    :param kind:

       version string kind: now (is alias of current), current, tag, or
       explicit semantic version

    :type kind: str
    :param copyright_start_year: copyright start year. Provide as an int
    :type copyright_start_year: int
    :param snippet_co:

       Snippet code, within a file, unique id of an editable region, aka snippet.
       Only necessary if allows for multiple snippets

    :type snippet_co: str
    """
    try:
        sc = SnipSphinxConf(path=path)
    except NotADirectoryError:
        msg_exc = "Expected a doc/ or docs/ folder"
        click.secho(msg_exc, fg="red")
        sys.exit(3)
    except FileNotFoundError:
        msg_exc = "Expected to find file, doc/conf.py or docs/conf.py"
        click.secho(msg_exc, fg="red")
        sys.exit(4)

    # From pyproject.toml, get project name
    try:
        _logger.info(f"path: {path}")
        path_pyproject = path.joinpath("pyproject.toml")
        _logger.info(f"path: {path_pyproject}")
        d_toml = get_pyproject_toml(path_pyproject)
        _logger.info(f"d_toml: {d_toml}")
    except (FileNotFoundError, PyProjectTOMLParseError):
        msg_exc = (
            f"pyproject.toml either not exists or validation fail. {path}\n"
            f"{traceback.format_exc()}"
        )
        click.secho(msg_exc, fg="red")
        sys.exit(5)
    package_name = d_toml.get("project", {}).get("name", None)

    if package_name is None:
        msg_exc = "From pyproject.toml, could not get package name"
        click.secho(msg_exc, fg="red")
        sys.exit(6)

    sc.contents(
        kind,
        package_name,
        copyright_start_year,
    )

    # existing_contents = sc._contents
    is_success = sc.replace(snippet_co=snippet_co)
    if not is_success:
        msg_exc = (
            "In sphinx [doc folder]/conf.py, snippet was not "
            f"replaced. Ensure snippet has this id: {snippet_co}"
        )
        click.secho(msg_exc, fg="red")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
