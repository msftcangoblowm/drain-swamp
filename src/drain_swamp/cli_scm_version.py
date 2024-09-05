"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Get scm version, limit to setuptool-scm codebase.

"""

import sys
from pathlib import Path

import click

# pep366 ...
# https://stackoverflow.com/a/34155199
if __name__ == "__main__" and __spec__ is None:  # pragma: no cover
    # Package not installed
    # python src/drain_swamp/cli_scm_version.py get
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
else:  # pragma: no cover
    pass

from drain_swamp.monkey.wrap_get_version import (
    scm_version,
    write_to_file,
)

entrypoint_name = "scm-version"  # noqa: F401

help_path = "The root directory [default: pyproject.toml directory]"
help_is_write = "Write flag. 1 write, 0 not write"
help_write_to = "Override version file relative path"

EPILOG_SCM_VERSION_GET = """
EXIT CODES

3 -- missing pyproject.toml or missing sections tool.drain-swamp and
     tool.pipenv-unlock

4 -- invalid semantic str. Skip. Do not write that nonsense to version file

"""
EPILOG_SCM_VERSION_WRITE = """
EXIT CODES

3 -- missing pyproject.toml or missing sections tool.drain-swamp and
     tool.pipenv-unlock

4 -- invalid semantic str. Skip. Do not write that nonsense to version file

"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
def main():
    """Command-line for scm-version. Prints usage"""


@main.command(
    "get",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_SCM_VERSION_GET,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
@click.option(
    "--is-write",
    "is_write",
    default=False,
    help=help_is_write,
    is_flag=True,
)
@click.option(
    "-w",
    "--write-to",
    "write_to",
    default=None,
    type=click.STRING,
    help=help_write_to,
)
def get_scm_version(path, is_write, write_to):
    """scm version, setuptools-scm codebase only.

    \f
    :param path:

       The root directory [default: pyproject.toml directory]

    :type path: pathlib.Path
    :param is_write: Default False. True to write to file otherwise don't write
    :type is_write: bool
    :param write_to: During testing provide alternative version file path
    :type write_to: str | None
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path_cwd = Path(path)
    else:  # pragma: no cover
        path_cwd = path

    # Both scm_version and write_to_file expect relative_to not package base folder
    path_relative_to = path_cwd.joinpath("pyproject.toml")
    relative_to_path = str(path_relative_to)

    str_scm_ver = scm_version(relative_to_path)

    click.echo(str_scm_ver)

    if is_write:
        try:
            write_to_file(relative_to_path, str_scm_ver, write_to=write_to)
        except LookupError as e:
            msg_warn = str(e)
            exit_code = 3
        except ValueError as e:
            # invalid semantic version str (from git?!)
            msg_warn = str(e)
            exit_code = 4
        else:
            exit_code = 0

        if exit_code != 0:
            click.secho(msg_warn, fg="red", err=True)
            sys.exit(exit_code)
        else:  # pragma: no cover
            pass
    else:  # pragma: no cover
        pass


@main.command(
    "write",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_SCM_VERSION_WRITE,
)
@click.argument("scm_ver")
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=help_path,
)
@click.option(
    "-w",
    "--write-to",
    "write_to",
    default=None,
    type=click.STRING,
    help=help_write_to,
)
def write_scm_version(scm_ver, path, write_to):
    """Write scm str to version file.

    \f
    :param scm_ver: version str
    :type scm_ver: str
    :param path:

       The root directory [default: pyproject.toml directory]

    :type path: pathlib.Path
    :param write_to: During testing provide alternative version file path
    :type write_to: str | None
    """
    # resolve causing conversion into a str. Should be Path
    if isinstance(path, str):  # pragma: no cover
        path_cwd = Path(path)
    else:  # pragma: no cover
        path_cwd = path

    # Both scm_version and write_to_file expect relative_to not package base folder
    path_relative_to = path_cwd.joinpath("pyproject.toml")
    relative_to_path = str(path_relative_to)

    # Possible for there to be no pyproject.toml or missing sections
    try:
        write_to_file(relative_to_path, scm_ver, write_to=write_to)
    except LookupError as e:
        # issue with pyproject.toml
        msg_warn = str(e)
        exit_code = 3
    except ValueError as e:
        # invalid semantic version str
        msg_warn = str(e)
        exit_code = 4
    else:
        exit_code = 0

    if exit_code != 0:
        # Write version file skipped
        click.secho(msg_warn, fg="red", err=True)
    else:  # pragma: no cover
        pass
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    """Process shield."""
    main()
