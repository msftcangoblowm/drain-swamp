import datetime
from pathlib import Path
from typing import (
    Any,
    ClassVar,
)

from .version_semantic import SemVersion

__all__ = ("SnipSphinxConf", "entrypoint_name")

entrypoint_name: str

class SnipSphinxConf:
    DOC_FOLDERS: ClassVar[tuple[str, str]]

    def __init__(self, path: Any | None = None) -> None: ...
    @classmethod
    def now(cls) -> datetime.datetime: ...
    @classmethod
    def now_to_str(cls, strftime_str: str) -> str: ...
    @property
    def path_abs(self) -> Path: ...
    def path_abs_init(self) -> None: ...
    @property
    def path_cwd(self) -> Path: ...
    @path_cwd.setter
    def path_cwd(self, val: Any | None) -> None: ...
    @property
    def SV(self) -> SemVersion | None: ...
    @property
    def author_name_left(self) -> str | None: ...
    def contents(
        self,
        kind: str,
        package_name: str,
        copyright_start_year: str,
    ) -> str: ...
    def replace(
        self,
        snippet_co: str | None = None,
    ) -> bool: ...
