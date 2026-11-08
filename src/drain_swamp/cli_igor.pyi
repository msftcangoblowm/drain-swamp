import logging
from pathlib import Path
from typing import Final

import click

_logger: logging.Logger
entrypoint_name: Final[str]
help_path: Final[str]
help_snippet_co: Final[str]
help_kind: Final[str]
EPILOG_BUILD: Final[str]
EPILOG_CHEATS: Final[str]
EPILOG_CURRENT_VERSION: Final[str]
EPILOG_EDITS: Final[str]
EPILOG_LIST: Final[str]
EPILOG_PRETAG: Final[str]
EPILOG_SCM_PAIR: Final[str]
EPILOG_SEED: Final[str]
EPILOG_TAG_VERSION: Final[str]

@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
def main() -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    help=help_path,
)
def seed(path: Path) -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
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
def edit(path: Path, kind: str, snippet_co: str | None = None) -> None: ...
@main.command(
    "list",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_LIST,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    help=help_path,
)
def snippets_list(path: Path) -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
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
def semantic_version_aware_build(
    path: Path, kind: str, package_name: str | None = None
) -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
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
def setuptools_scm_key_value_pair(path: Path, kind: str) -> None: ...
@main.command(
    "pretag",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_PRETAG,
)
@click.argument("ver", type=click.STRING)
def validate_tag(ver: str) -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    help=help_path,
)
def current_version(path: Path) -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    help=help_path,
)
def tag_version(path: Path) -> None: ...
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
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
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
def do_cheats(path: Path, kind: str) -> None: ...
