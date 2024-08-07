import logging
from collections.abc import (
    Generator,
    Sequence,
)
from dataclasses import (
    InitVar,
    dataclass,
)
from pathlib import Path
from typing import (
    Any,
    Final,
)

from .backend_abc import BackendType

__all__ = (
    "lock_compile",
    "refresh_links",
    "unlock_compile",
)

_logger: Final[logging.Logger]
is_module_debug: Final[bool]

def is_piptools() -> bool: ...
def _create_symlinks_relative(src: str, dest: str, cwd_path: str) -> None: ...
def _maintain_symlink(path_cwd: Path, abspath_out: Path) -> None: ...
def lock_compile(inst: BackendType) -> Generator[Path, None, None]: ...
def strip_inline_comments(val: str) -> str: ...
@dataclass
class InFile:
    relpath: str
    stem: str
    constraints: set[str] = ...
    requirements: set[str] = ...

    @staticmethod
    def check_path(cwd: Path, path_to_check: Any) -> None: ...
    def abspath(self, path_package_base: Path) -> Path: ...
    @property
    def depth(self) -> int: ...
    def resolve(self, constraint: str, requirements: set[str]) -> None: ...
    def __hash__(self) -> int: ...
    def __eq__(self, right: object) -> bool: ...

@dataclass
class InFiles:
    cwd: Path
    in_files: InitVar[list[Path]]
    _files: set[InFile] = ...
    _zeroes: set[InFile] = ...

    def __post_init__(self, in_files: Sequence[Path]) -> None: ...
    @property
    def files(self) -> Generator[InFile, None, None]: ...
    @files.setter
    def files(self, val: Any) -> None: ...
    @property
    def zeroes(self) -> Generator[InFile, None, None]: ...
    @zeroes.setter
    def zeroes(self, val: Any) -> None: ...
    def in_generic(self, val: Any, set_name: str | None = "files") -> bool: ...
    def in_zeroes(self, val: Any) -> bool: ...
    def __contains__(self, val: Any) -> bool: ...
    def get_by_relpath(
        self,
        relpath: str,
        set_name: str | None = "files",
    ) -> InFile | None: ...
    def move_zeroes(self) -> None: ...
    def resolve_zeroes(self) -> None: ...
    def resolution_loop(self) -> None: ...
    def write(self) -> Generator[Path, None, None]: ...

def unlock_compile(inst: BackendType) -> Generator[Path, None, None]: ...
def refresh_links(inst: BackendType, is_set_lock: bool | None = None) -> None: ...
