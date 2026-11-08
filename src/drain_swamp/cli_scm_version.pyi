from pathlib import Path
from typing import Final

import click

entrypoint_name: Final[str]
help_path: Final[str]
help_is_write: Final[str]
help_write_to: Final[str]
EPILOG_SCM_VERSION_GET: Final[str]
EPILOG_SCM_VERSION_WRITE: Final[str]

@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
def main() -> None: ...
@main.command(
    "get",
    context_settings={"ignore_unknown_options": True},
    epilog=EPILOG_SCM_VERSION_GET,
)
@click.option(
    "-p",
    "--path",
    default=Path.cwd(),
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
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
def get_scm_version(path: Path, is_write: bool, write_to: str | None) -> None: ...
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
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
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
def write_scm_version(scm_ver: str, path: Path, write_to: str | None) -> None: ...
