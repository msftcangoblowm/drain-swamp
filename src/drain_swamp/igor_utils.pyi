import logging
from pathlib import Path

_logger: logging.Logger
__all__ = (
    "seed_changelog",
    "edit_for_release",
    "build_package",
)

def update_file(fname: str, pattern: str, replacement: str) -> None: ...
def seed_changelog(path_cwd: Path) -> None: ...
def edit_for_release(
    path_cwd: Path,
    kind: str,
    snippet_co: str | None = None,
) -> int | None: ...
def build_package(
    path: Path,
    kind: str,
    package_name: str | None = None,
) -> bool: ...
