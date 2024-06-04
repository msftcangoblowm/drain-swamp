"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

pipenv-unlock package entrypoint

.. seealso::

   `click epilog hell <https://stackoverflow.com/q/44124680>`_

"""

import sys
import traceback
from pathlib import Path

import click

# pep366 ...
# https://stackoverflow.com/a/34155199
if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    # Package not installed
    # python src/drain_swamp/cli_unlock.py unlock --snip=little_shop_of_horrors_shrine_candles
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
    # python -m drain_swamp.cli_unlock lock --snip=little_shop_of_horrors_shrine_candles
    tmp_pkg = "drain_swamp"
    path_pkg_base_dir = Path(__file__).parent.parent
    sys.path.insert(1, str(path_pkg_base_dir))
    mod = __import__(tmp_pkg)
    sys.modules[tmp_pkg] = mod
    __package__ = tmp_pkg
else:
    # pipenv-unlock unlock --snip=little_shop_of_horrors_shrine_candles
    # pipenv-unlock lock --snip=little_shop_of_horrors_shrine_candles
    __package__ = "drain_swamp"
# pep366 ...done

from .backend_abc import BackendType
from .backend_setuptools import BackendSetupTools  # noqa: F401
from .constants import (
    SUFFIX_LOCKED,
    SUFFIX_UNLOCKED,
    __version_app,
)
from .exceptions import (
    BackendNotSupportedError,
    MissingRequirementsFoldersFiles,
    PyProjectTOMLParseError,
    PyProjectTOMLReadError,
)
from .lock_toggle import (
    lock_compile,
    unlock_compile,
)
from .snip import (
    ReplaceResult,
    Snip,
)

# taken from pyproject.toml
entrypoint_name = "pipenv-unlock"  # noqa: F401

help_path = "The root directory [default: pyproject.toml directory]"
help_required = "relative to --path, required dependencies .in file"
help_optionals = (
    "relative to --path, optional dependencies .in file. Can be used multiple times"
)
help_additional_folder = (
    "Additional folder(s), not already known implicitly, containing .in "
    "files. A relative_path. Can be used multiple times"
)
help_snippet_co = (
    "Snippet code, within a file, unique id of an editable region, aka snippet. "
    "Only necessary if allows for multiple snippets"
)

EPILOG_LOCK_UNLOCK = """
EXIT CODES

0 -- Evidently sufficient effort put into unittesting. Job well done, beer on me!

1 -- Unused. Reason: too generic

2 -- Unused. Reason: Bad taste left in mouth after experience with argparse

3 -- path given for config file either not a file or not read write

4 -- pyproject.toml config file parse issue. Use validate-pyproject on it then try again

5 -- Backend not supported. Need to add support for that backend. Submit an issue

6 -- The pyproject.toml depends on the requirements folders and files. Create them

7 -- For locking dependencies, pip-tools package must be installed. Not installed

8 -- The snippet is invalid. Either nested snippets or start stop token out of order. Fix the snippet then try again

9 -- In pyproject.toml, there is no snippet with that snippet code
"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version_app)
def main():
    """Command-line for pipenv-unlock. Prints usage"""


@main.command(
    "lock",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_LOCK_UNLOCK,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help=help_path,
)
@click.option(
    "-r",
    "--required",
    default=None,
    type=(str, click.Path(exists=False, file_okay=True, dir_okay=False)),
    help=help_required,
    nargs=2,
)
@click.option(
    "-o",
    "--optional",
    "optionals",
    type=(str, click.Path(exists=False, file_okay=True, dir_okay=False)),
    help=help_optionals,
    multiple=True,
    nargs=2,
)
@click.option(
    "-d",
    "--dir",
    "additional_folders",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    multiple=True,
    help=help_additional_folder,
)
@click.option(
    "-s",
    "--snip",
    "snippet_co",
    default=None,
    type=click.STRING,
    help=help_snippet_co,
)
def dependencies_lock(path, required, optionals, additional_folders, snippet_co):
    """Choose to have dependencies locked

    Disadvantages

    1. FOSS is ``as-is``, largely unpaid work, often lacks necessary
       skillset, often doesn't care to do tedious tasks, is pressed for
       time, and live happens. These are the people supposed to be
       making packages for production use?! Having such expectations
       is ridiculous and conflicts with the human condition

    2. package quickly becomes unusable when, not if, the author is no longer
       maintaining the package

    3. Non-experts might not be using pipenv, only pip. Almost guaranteeing
       dependency hell. ``pip`` won't have what it needs to resolve
       dependency version conflicts

    4. ``pipenv`` says don't automate updating dependency lock files thru CI/CD

    5. ``pip-tools``, mistakes occur, choosing wrong dependency version.
       Had this occur. Latest version is a post release (python-dateutil-2.9.0.post0
       Sometimes choose previous release and other times not. Causing dependency hell

    Advantage

    1. Job security. Knowledgable eyeballs **must** regularly update
       dependency version locks

    2. ``pipenv`` discourages attackers setting up alternative repository hosts
       ``pypi.org`` and swapping out an obscure package with their own.

    3. The stars align in the cosmos, miraculously, all package authors regularly
       update their packages dependencys' locks. Get that warm feeling inside
       knowing we are alive, loved, and appreciated. We shout,
       ``it's a miracle!`` and be right!

    Usage

    .. code-block:: shell

       pipenv-unlock lock --snip="little_shop_of_horrors_shrine_candles"

    \f

    :param path:

       The root directory [default: pyproject.toml directory]

    :type path: pathlib.Path
    :param required:

       relative to --path, required dependencies .in file

    :type required: tuple[str, pathlib.Path]
    :param optionals:

       relative to --path, optional dependencies .in file. Can be used multiple times

    :type optionals: collections.abc.Sequence[tuple[str, pathlib.Path]]
    :param additional_folders:

       Additional folder(s), not already known implicitly, containing .in
       files. A relative_path. Can be used multiple times

    :type additional_folders: collections.abc.Sequence[pathlib.Path]
    :param snippet_co:

       Snippet code, within a file, unique id of an editable region, aka snippet.
       Only necessary if allows for multiple snippets

    :type snippet_co: str | None
    """

    # No user input validation yet
    # Sequence[tuple[str, pathlib.Path]] | None --> dict[str, Path]
    has_optionals = (
        optionals is not None and isinstance(optionals, tuple) and len(optionals) > 0
    )
    if has_optionals:
        d_optionals = {}
        for target, relative_path in optionals:
            if target not in d_optionals.keys():
                d_optionals[target] = relative_path
            else:  # pragma: no cover
                pass
    else:
        d_optionals = {}

    try:
        inst = BackendType.load_factory(
            path,
            required=required,
            optionals=d_optionals,
        )
    except PyProjectTOMLReadError:
        msg_exc = (
            f"Either not a file or lacks read permissions. {traceback.format_exc()}"
        )
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(3)
    except PyProjectTOMLParseError:
        msg_exc = f"Cannot parse pyproject.toml. {traceback.format_exc()}"
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(4)
    except BackendNotSupportedError:
        msg_exc = f"No support yet for this Python packaging backend. {traceback.format_exc()}"
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(5)

    try:
        new_contents = inst.compose(SUFFIX_LOCKED)
    except MissingRequirementsFoldersFiles:
        msg_exc = (
            "Missing requirements folders and files. Prepare these "
            f"{traceback.format_exc()}"
        )
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(6)

    # create .lock files in their respective folders
    gen = lock_compile(inst)
    try:
        list(gen)  # execute generator
    except AssertionError:
        msg_exc = (
            "pip-tools is required to lock package dependencies. Install "
            f"it. {traceback.format_exc()}"
        )
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(7)

    # update snippet
    fname = path / "pyproject.toml"
    snip = Snip(fname, is_quiet=True)
    is_success = snip.replace(new_contents, id_=snippet_co)
    if is_success == ReplaceResult.VALIDATE_FAIL:
        msg_exc = (
            "Snippet is invalid. Validation failed. Either nested or "
            "unmatched start end tokens"
        )
        click.secho(msg_exc, fg="red")
        sys.exit(8)
    elif is_success == ReplaceResult.NO_MATCH:
        msg_exc = (
            f"In pyproject.toml, there is no snippet with snippet code {snippet_co}"
        )
        click.secho(msg_exc, fg="red")
        sys.exit(9)
    else:
        sys.exit(0)


@main.command(
    "unlock",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_LOCK_UNLOCK,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help=help_path,
)
@click.option(
    "-r",
    "--required",
    default=None,
    type=(str, click.Path(exists=False, file_okay=True, dir_okay=False)),
    help=help_required,
    nargs=2,
)
@click.option(
    "-o",
    "--optional",
    "optionals",
    type=(str, click.Path(exists=False, file_okay=True, dir_okay=False)),
    help=help_optionals,
    nargs=2,
    multiple=True,
)
@click.option(
    "-d",
    "--dir",
    "additional_folders",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    multiple=True,
    help=help_additional_folder,
)
@click.option(
    "-s",
    "--snip",
    "snippet_co",
    default=None,
    type=click.STRING,
    help=help_snippet_co,
)
def dependencies_unlock(path, required, optionals, additional_folders, snippet_co):
    """Consciously choose not to lock package dependencies

    Know that might not be available or always paying constant attention.
    Whilst package dependency lock requires frequent updating.

    It's a big ask, considering:

    - distracted by other projects and paid jobs

    - cynical

    - intend to pick up a drug habit, die, or discover girls

    Usage

    .. code-block:: shell

       pipenv-unlock unlock --snip="little_shop_of_horrors_shrine_candles"

    \f

    :param path:

       The root directory [default: pyproject.toml directory]

    :type path: pathlib.Path
    :param required:

       relative to --path, required dependencies .in file

    :type required: tuple[str, pathlib.Path]
    :param optionals:

       relative to --path, optional dependencies .in file. Can be used multiple times

    :type optionals: collections.abc.Sequence[tuple[str, pathlib.Path]]
    :param additional_folders:

       Additional folder(s), not already known implicitly, containing .in
       files. A relative_path. Can be used multiple times

    :type additional_folders: collections.abc.Sequence[pathlib.Path]
    :param snippet_co:

       Snippet code, within a file, unique id of an editable region, aka snippet.
       Only necessary if allows for multiple snippets

    :type snippet_co: str | None
    """

    # No user input validation yet
    # Sequence[tuple[str, pathlib.Path]] | None --> dict[str, Path]
    has_optionals = (
        optionals is not None and isinstance(optionals, tuple) and len(optionals) > 0
    )
    if has_optionals:
        d_optionals = {}
        for target, relative_path in optionals:
            if target not in d_optionals.keys():
                d_optionals[target] = relative_path
            else:  # pragma: no cover
                pass
    else:
        d_optionals = {}

    try:
        inst = BackendType.load_factory(
            path,
            required=required,
            optionals=d_optionals,
        )
    except PyProjectTOMLReadError:
        msg_exc = (
            f"Either not a file or lacks read permissions. {traceback.format_exc()}"
        )
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(3)
    except PyProjectTOMLParseError:
        msg_exc = f"Cannot parse pyproject.toml. {traceback.format_exc()}"
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(4)
    except BackendNotSupportedError:
        msg_exc = f"No support yet for this Python packaging backend. {traceback.format_exc()}"
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(5)

    # get contents for update to pyproject.toml
    try:
        new_contents = inst.compose(SUFFIX_UNLOCKED)
    except MissingRequirementsFoldersFiles:
        msg_exc = (
            "Missing requirements folders and files. Prepare these "
            f"{traceback.format_exc()}"
        )
        # raise click.ClickException(msg_exc)
        click.secho(msg_exc, fg="red")
        sys.exit(6)

    # update snippet -- pyproject.toml
    fname = path / "pyproject.toml"
    snip = Snip(fname, is_quiet=False)
    is_success = snip.replace(new_contents, id_=snippet_co)
    if is_success == ReplaceResult.VALIDATE_FAIL:
        msg_exc = (
            "Snippet is invalid. Validation failed. Either nested or "
            "unmatched start end tokens"
        )
        click.secho(msg_exc, fg="red")
        sys.exit(8)
    elif is_success == ReplaceResult.NO_MATCH:
        msg_exc = (
            f"In pyproject.toml, there is no snippet with snippet code {snippet_co}"
        )
        click.secho(msg_exc, fg="red")
        sys.exit(9)
    else:
        pass

    # creates / writes .unlock files
    gen = unlock_compile(inst)
    list(gen)  # execute generator


if __name__ == "__main__":  # pragma: no cover
    main()
