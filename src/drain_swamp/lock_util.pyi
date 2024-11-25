from pathlib import Path
from typing import Any

ENDINGS: tuple[str, str, str, str, str, str]
__all__ = (
    "ENDINGS",
    "abspath_relative_to_package_base_folder",
    "is_shared",
    "replace_suffixes_last",
    "is_suffixes_ok",
    "check_relpath",
)

def is_shared(file_name: str) -> bool: ...
def replace_suffixes_last(
    abspath_f: Any,
    suffix_last: str,
) -> Path: ...
def is_suffixes_ok(path_either: Any) -> Path: ...
def check_relpath(cwd: Path, path_to_check: Any) -> None: ...
def abspath_relative_to_package_base_folder(
    abspath_cwd: Path,
    abspath_f: Path,
    constraint_relpath: str,
) -> Path: ...
