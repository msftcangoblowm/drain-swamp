from collections.abc import Sequence
from pathlib import Path
from typing import Any

__all__ = (
    "is_ok",
    "is_relative_required",
    "is_iterable_not_str",
)

def is_ok(test: Any | None) -> bool: ...
def is_iterable_not_str(mixed: Any | None) -> bool: ...
def is_relative_required(
    path_relative: Path | None = None,
    extensions: Sequence[str] = ...,
) -> bool: ...
def click_bool(val: str | None = None) -> bool | None: ...
