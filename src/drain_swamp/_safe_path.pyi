from pathlib import (
    Path,
    PurePath,
    PurePosixPath,
    PureWindowsPath,
)

__all__ = (
    "fix_relpath",
    "is_linux",
    "is_macos",
    "is_win",
    "replace_suffixes",
    "resolve_path",
    "resolve_joinpath",
)

def is_linux() -> bool: ...
def is_macos() -> bool: ...
def is_win() -> bool: ...
def _to_purepath(relpath_b: PurePath | Path | str) -> type[PurePath]: ...
def resolve_path(str_cmd: str) -> str: ...
def fix_relpath(
    relpath_b: PurePath | Path | str,
) -> str: ...
def resolve_joinpath(
    abspath_a: PurePath | Path,
    relpath_b: PurePath | Path | str,
) -> PureWindowsPath | PurePosixPath | type[Path]: ...
def replace_suffixes(
    abspath_a: PurePath | Path,
    suffixes: str,
) -> PurePath | Path: ...
