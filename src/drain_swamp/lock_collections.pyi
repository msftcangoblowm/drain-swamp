import dataclasses
import sys
from collections.abc import (
    Collection,
    Generator,
    Iterator,
)
from pathlib import Path
from typing import Any

from .lock_datum import InFileType
from .lock_filepins import FilePins
from .pep518_venvs import VenvMapLoader

if sys.version_info >= (3, 11):  # pragma: no cover py-ge-311-else
    from typing import Self
else:  # pragma: no cover py-ge-311
    from typing_extensions import Self

__all__ = ("Ins",)

@dataclasses.dataclass
class Ins(Collection[FilePins]):
    loader: VenvMapLoader
    venv_path: dataclasses.InitVar[str]
    _venv_relpath: str
    _file_pins: list[FilePins]
    _iter: Iterator[FilePins]
    _files: set[FilePins]
    _zeroes: set[FilePins]

    def __contains__(self, item: Any) -> bool: ...
    def __iter__(self) -> Self: ...
    def __len__(self) -> int: ...
    def __next__(self) -> FilePins: ...
    def __post_init__(
        self,
        venv_path: str | Path,
    ) -> None: ...
    @property
    def files(self) -> Generator[FilePins, None, None]: ...
    @files.setter
    def files(self, val: Any) -> None: ...
    @property
    def files_len(self) -> int: ...
    def get_by_abspath(
        self,
        abspath_f: Path,
        set_name: InFileType | None = ...,
    ) -> Path: ...
    def in_files(self, val: Any) -> bool: ...
    def in_zeroes(self, val: Any) -> bool: ...
    def load(self, suffix_last: str | None = ...) -> None: ...
    def move_zeroes(self) -> None: ...
    @property
    def path_cwd(self) -> Path: ...
    def resolution_loop(self) -> None: ...
    def resolve_zeroes(self) -> None: ...
    def write(self) -> None: ...
    @property
    def zeroes(self) -> Generator[FilePins, None, None]: ...
    @zeroes.setter
    def zeroes(self, val: Any) -> None: ...
    @property
    def zeroes_len(self) -> int: ...

def unlock_compile(
    loader: VenvMapLoader,
    venv_relpath: Any | None,
) -> Generator[Path, None, None]: ...
