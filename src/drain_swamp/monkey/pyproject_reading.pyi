from collections.abc import Callable
from pathlib import Path
from typing import (
    Any,
    TypedDict,
)

from typing_extensions import TypeAlias

TOML_RESULT: TypeAlias = dict[str, Any]
TOML_LOADER: TypeAlias = Callable[[str], TOML_RESULT]

__all__ = (
    "TOML_LOADER",
    "TOML_RESULT",
    "read_toml_content",
    "load_toml_or_inline_map",
)

def read_toml_content(
    path: Path,
    default: TOML_RESULT | None = None,
) -> TOML_RESULT: ...

class _CheatTomlData(TypedDict):  # noqa: Y049
    cheat: dict[str, Any]

def load_toml_or_inline_map(
    data: Any | None,
) -> dict[str, Any]: ...
