import logging
from functools import cache
from pathlib import Path
from typing import (
    Any,
    Final,
)

_logger: logging.Logger
__all__ = ("PackageMetadata",)

AUTHOR_NAME_FALLBACK: Final[str]

@cache
def get_author_and_email(app_name: str) -> tuple[str, str | None]: ...

class PackageMetadata:
    __slots__ = ("_app_name", "_full_name", "_email", "_d_pyproject_toml")
    def __init__(self, app_name: Any, path: Path | None = None) -> None: ...
    @property
    def app_name(self) -> str: ...
    @app_name.setter
    def app_name(self, val: Any) -> None: ...
    @property
    def full_name(self) -> str: ...
    @property
    def left_name(self) -> str: ...
    @property
    def email(self) -> str | None: ...
    @property
    def d_pyproject_toml(self) -> dict[str, Any] | None: ...
