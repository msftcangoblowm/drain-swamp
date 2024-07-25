import os
from collections.abc import Sequence
from pathlib import Path

__all__ = ("run_cmd",)

def run_cmd(
    cmd: Sequence[str],
    cwd: Path | None = None,
    env: os._Environ[str] | None = None,
) -> tuple[str | None, str | None, int | None, str | None]: ...
