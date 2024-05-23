import logging
from collections.abc import Generator
from pathlib import Path
from typing import Final

from .backend_abc import BackendType

__all__ = (
    "lock_compile",
    "unlock_create",
)

_logger: Final[logging.Logger]

def is_piptools() -> bool: ...
def lock_compile(inst: BackendType) -> Generator[Path, None, None]: ...
def unlock_create(inst: BackendType) -> None: ...
