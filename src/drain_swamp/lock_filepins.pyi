import dataclasses
import sys
from collections.abc import (
    Collection,
    Generator,
    Hashable,
    Iterator,
)
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):  # pragma: no cover py-ge-311-else
    from typing import Self
else:  # pragma: no cover py-ge-311
    from typing_extensions import Self

from .lock_datum import PinDatum
from .pep518_venvs import VenvMapLoader

__all__ = (
    "FilePins",
    "get_path_cwd",
)

def get_path_cwd(loader: VenvMapLoader) -> Path: ...
@dataclasses.dataclass
class FilePins(Collection[PinDatum], Hashable):
    file_abspath: Path
    _pins: list[PinDatum]
    _iter: Iterator[PinDatum]
    constraints: set[str]
    requirements: set[str]

    def __post_init__(self) -> None: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> PinDatum: ...
    def __contains__(self, item: Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __eq__(self, right: object) -> bool: ...
    def __lt__(self, right: object) -> bool: ...
    def relpath(self, loader: VenvMapLoader) -> Path: ...
    @property
    def depth(self) -> int: ...
    def resolve(
        self,
        constraint: str,
        plural: str = ...,
        singular: str = ...,
    ) -> None: ...
    def packages_save_to_parent(
        self,
        fpins: list[PinDatum],
        requirements: set[str],
    ) -> None: ...
    def by_pkg(self, pkg_name: Any) -> list[PinDatum]: ...
    def by_pin_or_qualifier(self) -> Generator[PinDatum, None, None]: ...
