from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = (
    "find_project_root",
    "find_pyproject_toml",
)

def _is_ok(test: Any | None) -> bool: ...
@lru_cache
def find_project_root(
    srcs: Sequence[Any] | None,
    stdin_filename: str | None = None,
) -> tuple[Path, str]: ...
def find_pyproject_toml(
    path_search_start: tuple[str, ...],
    stdin_filename: str | None = None,
) -> str | None: ...
