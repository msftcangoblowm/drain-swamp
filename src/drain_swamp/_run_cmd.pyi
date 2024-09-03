import os
from collections.abc import Sequence
from pathlib import Path

__all__ = (
    "run_cmd",
    "resolve_path",
)

def resolve_path(str_cmd: str) -> str: ...
def run_cmd(
    cmd: Sequence[str],
    cwd: Path | None = None,
    env: os._Environ[str] | None = None,
) -> tuple[str | None, str | None, int | None, str | None]: ...
