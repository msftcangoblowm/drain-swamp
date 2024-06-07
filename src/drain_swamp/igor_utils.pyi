import logging
from pathlib import Path
from typing import Final

__all__ = (
    "seed_changelog",
    "edit_for_release",
    "build_package",
    "pretag",
)
UNRELEASED: Final[str]
SCRIV_START: Final[str]
COPYRIGHT_START_YEAR_FALLBACK: Final[int]
REGEX_COPYRIGHT_LINE: Final[str]

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
def pretag(tag: str) -> tuple[bool, str]: ...
def get_current_version(path: Path) -> str | None: ...
