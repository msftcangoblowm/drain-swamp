import logging
from collections.abc import (
    Generator,
    Iterator,
    MutableSet,
    Sequence,
)
from dataclasses import dataclass
from functools import singledispatch
from pathlib import Path
from typing import (  # noqa: Y037
    Any,
    Final,
    TypeVar,
    Union,
)

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from typing_extensions import (
    Self,
    TypeAlias,
)

from .lock_infile import InFiles
from .pep518_venvs import (
    VenvMapLoader,
    VenvReq,
)

DC_SLOTS: dict[str, bool]
is_module_debug: Final[bool]
_logger = logging.Logger

@dataclass(**DC_SLOTS)
class Pin:
    file_abspath: Path
    pkg_name: str
    line: str
    specifiers: list[str] = ...

    def __hash__(self) -> int: ...
    def __post_init__(self) -> None: ...
    @staticmethod
    def is_pin(specifiers: list[str]) -> bool: ...
    @property
    def qualifiers(self) -> list[str]: ...

# This is a different view.
# Within one venv, all .lock files, organizes Pin by package name
PinsByPkg: TypeAlias = dict[str, list[Pin]]
_T = TypeVar("_T", bound=Pin)
PkgsWithIssues: TypeAlias = dict[str, dict[str, Union[Version, set[Version]]]]

class Pins(MutableSet[_T]):
    _pins: set[_T]
    _iter: Iterator[_T]
    __slots__ = ("_pins", "_iter")

    def __init__(
        self,
        pins: Any,
    ) -> None: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...
    def __contains__(self, item: Any) -> bool: ...
    def add(self, item: Any) -> None: ...
    def discard(self, item: Any) -> None: ...
    @staticmethod
    def from_loader(
        loader: VenvMapLoader,
        venv_path: str | Path,
        suffix: str = ...,
        filter_by_pin: bool | None = True,
    ) -> set[_T]: ...
    @staticmethod
    def subset_req(
        venv_reqs: list[VenvReq],
        pins: Pins[_T],
        req_relpath: str,
    ) -> set[_T]: ...
    @staticmethod
    def by_pkg(
        loader: VenvMapLoader,
        venv_path: str,
        suffix: str | None = ...,
        filter_by_pin: bool | None = True,
    ) -> PinsByPkg: ...
    @classmethod
    def by_pkg_with_issues(
        cls,
        loader: VenvMapLoader,
        venv_path: str,
    ) -> tuple[PinsByPkg, PkgsWithIssues]: ...
    @staticmethod
    def has_discrepancies(d_by_pkg: PinsByPkg) -> dict[str, Version]: ...
    @staticmethod
    def filter_pins_of_pkg(pins_current: Pins[_T], pkg_name: str) -> Pins[_T]: ...
    @classmethod
    def qualifiers_by_pkg(
        cls,
        loader: VenvMapLoader,
        venv_path: str,
    ) -> dict[str, str]: ...

def _wrapper_pins_by_pkg(
    loader: VenvMapLoader,
    venv_path: str,
    suffix: str | None = ...,
    filter_by_pin: bool | None = True,
) -> PinsByPkg: ...
@dataclass(**DC_SLOTS)
class Resolvable:
    venv_path: str | Path
    pkg_name: str
    qualifiers: str
    nudge_unlock: str
    nudge_lock: str

@dataclass(**DC_SLOTS)
class UnResolvable:
    venv_path: str
    pkg_name: str
    qualifiers: str
    sss: set[SpecifierSet]
    v_highest: Version
    v_others: set[Version]
    pins: Pins[Pin]

    def pprint_pins(self) -> str: ...

@dataclass(**DC_SLOTS)
class ResolvedMsg:
    abspath_f: Path
    nudge_pin_line: str

def get_reqs(
    loader: VenvMapLoader,
    venv_path: str | None = None,
    suffix_last: str = ...,
) -> tuple[Path]: ...
def get_issues(
    loader: VenvMapLoader,
    venv_path: str,
) -> tuple[list[Resolvable], list[UnResolvable]]: ...
def fix_resolvables(
    resolvables: Sequence[Resolvable],
    loader: VenvMapLoader,
    venv_path: str,
    is_dry_run: Any | None = False,
) -> tuple[list[ResolvedMsg], list[tuple[str, str, Resolvable, Pin]]]: ...
def fix_requirements(
    loader: VenvMapLoader,
    is_dry_run: Any | None = False,
) -> tuple[
    dict[str, ResolvedMsg],
    dict[str, UnResolvable],
    dict[str, tuple[str, Resolvable, Pin]],
]: ...
def filter_by_venv_relpath(
    loader: VenvMapLoader,
    venv_current_relpath: str | None,
) -> tuple[tuple[Path], InFiles]: ...
def unlock_compile(loader: VenvMapLoader) -> Generator[Path, None, None]: ...
@singledispatch
def prepare_pairs(t_ins: object) -> Generator[tuple[str, str], None, None]: ...
@prepare_pairs.register(tuple)
def _(t_ins: tuple[Path]) -> Generator[tuple[str, str], None, None]: ...
@prepare_pairs.register
def _(
    in_files: InFiles,
    path_cwd: Path | None = None,
) -> Generator[tuple[str, str], None, None]: ...
def _compile_one(
    in_abspath: str,
    lock_abspath: str,
    ep_path: str,
    path_cwd: Path,
    context: str | None = None,
    timeout: Any = 15,
) -> tuple[Path | None, None | str]: ...
def lock_compile(
    loader: VenvMapLoader,
    venv_relpath: str,
    timeout: Any = 15,
) -> tuple[tuple[str, ...], tuple[str, ...]]: ...
def is_timeout(failures: tuple[str, ...]) -> bool: ...
def _postprocess_abspath_to_relpath(path_out: Path, path_parent: Path) -> None: ...
