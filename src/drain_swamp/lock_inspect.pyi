import logging
import sys
from collections.abc import (
    Generator,
    Iterator,
    MutableSet,
    Sequence,
)
from pathlib import Path
from typing import (  # noqa: Y037
    Any,
    Final,
    TypeVar,
)

from .lock_datum import Pin
from .lock_discrepancy import (
    PkgsWithIssues,
    Resolvable,
    ResolvedMsg,
    UnResolvable,
)
from .lock_infile import InFiles
from .pep518_venvs import (
    VenvMapLoader,
    VenvReq,
)

if sys.version_info >= (3, 10):  # pragma: no cover py-gte-310-else
    from typing import TypeAlias
else:  # pragma: no cover py-gte-310
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 11):  # pragma: no cover py-gte-311-else
    from typing import Self
else:  # pragma: no cover py-gte-311
    from typing_extensions import Self

DC_SLOTS: dict[str, bool]
is_module_debug: Final[bool]
_logger = logging.Logger

# This is a different view.
# Within one venv, all .lock files, organizes Pin by package name
PinsByPkg: TypeAlias = dict[str, list[Pin]]
_T = TypeVar("_T", bound=Pin)

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
