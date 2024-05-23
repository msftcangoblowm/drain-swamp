from collections.abc import Sequence
from pathlib import Path
from typing import Final

entrypoint_name: Final[str]

help_pyproject_toml: Final[str]
help_required: Final[str]
help_optionals: Final[str]
help_extras: Final[str]

def main() -> None: ...
def dependencies_lock(
    path: Path,
    required: Path | None,
    optionals: Sequence[Path] = (),
    extras: Sequence[str] = (),
    additional_folders: Sequence[Path] = (),
    snippet_co: str | None = None,
) -> None: ...
def dependencies_unlock(
    path: Path,
    required: Path | None,
    optionals: Sequence[Path] = (),
    extras: Sequence[str] = (),
    additional_folders: Sequence[Path] = (),
    snippet_co: str | None = None,
) -> None: ...
