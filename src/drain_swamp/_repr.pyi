from pathlib import Path
from typing import Any

__all__ = (
    "repr_dict_str_path",
    "repr_set_path",
    "repr_path",
)

def _is_win() -> bool: ...
def _fix_bool(
    val: Any,
    default: bool = False,
) -> bool: ...
def _append_comma(
    str_a: str,
    is_condition: bool,
) -> str: ...
def repr_dict_str_path(
    k: str,
    d_repr: dict[str, Path],
    is_last: bool = False,
) -> str: ...
def repr_set_path(
    k: str,
    set_repr: set[Path],
    is_last: bool = False,
) -> str: ...
def repr_path(
    k: str,
    path: Path,
    is_last: bool = False,
) -> str: ...
