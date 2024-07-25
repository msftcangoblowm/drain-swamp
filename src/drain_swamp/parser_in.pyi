from collections.abc import Mapping
from pathlib import Path
from typing import Any

__all__ = ("TomlParser",)

class TomlParser:
    def __init__(
        self,
        path: Any | None,
        raise_exceptions: Any | None = False,
    ) -> None: ...
    @property
    def path_file(self) -> Path | None: ...
    @property
    def d_pyproject_toml(self) -> Mapping[str, Any] | None: ...
    @classmethod
    def resolve(cls, path_config: Any | None) -> Path: ...
    def _get_pyproject_toml(self, path_config: Any | None) -> Mapping[str, Any]: ...
