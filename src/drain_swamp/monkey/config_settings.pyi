import logging
from pathlib import Path
from typing import (
    Any,
    ClassVar,
)

__all__ = ("ConfigSettings",)

log: logging.Logger

class ConfigSettings:
    SECTION_NAME: ClassVar[str]
    ENVIRON_KEY: ClassVar[str]
    FILE_NAME_DEFAULT: ClassVar[str]

    __slots__: ClassVar[tuple[str]] = ("_file_name",)
    def __init__(self, file_name: str | None = None) -> None: ...
    @classmethod
    def get_abs_path(cls) -> str | None: ...
    @classmethod
    def set_abs_path(cls, val: Any) -> None: ...
    @classmethod
    def remove_abs_path(cls) -> None: ...
    @property
    def file_name(self) -> str: ...
    @file_name.setter
    def file_name(self, val: Any) -> None: ...
    def read(self) -> dict[str, Any]: ...
    def write(
        self,
        path_dir: Path,
        toml_contents: str,
    ) -> None: ...
    @classmethod
    def get_section_dict(
        cls,
        path_dir: Path,
        toml_contents: str,
        file_name: str | None = None,
    ) -> dict[str, Any]: ...
