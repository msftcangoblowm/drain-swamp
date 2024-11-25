import logging
from collections.abc import Sequence
from typing import (
    Any,
    Final,
)

from .lock_collections import Ins
from .lock_datum import (
    DatumByPkg,
    Pin,
    PinDatum,
)
from .lock_discrepancy import (
    Resolvable,
    ResolvedMsg,
    UnResolvable,
)
from .pep518_venvs import VenvMapLoader

is_module_debug: Final[bool]
_logger: Final[logging.Logger]

def _get_qualifiers(d_subset: DatumByPkg) -> dict[str, str]: ...
def _load_once(
    ins: Ins,
    locks: Ins,
    venv_relpath: str,
) -> tuple[list[Resolvable], list[UnResolvable]]: ...
def _fix_resolvables(
    resolvables: Sequence[Resolvable],
    locks: Ins,
    venv_relpath: str,
    is_dry_run: bool | None = False,
    suffixes: tuple[str, ...] = ...,
) -> tuple[list[ResolvedMsg], list[tuple[str, str, Resolvable, Pin | PinDatum]]]: ...

class Fixing:
    _ins: Ins
    _locks: Ins
    _venv_relpath: str
    _loader: VenvMapLoader

    def __init__(self, loader: VenvMapLoader, venv_relpath: str) -> None: ...
    def get_issues(self) -> None: ...
    def fix_resolvables(self, is_dry_run: bool | None = False) -> None: ...
    @property
    def resolvables(self) -> list[Resolvable]: ...
    @property
    def resolvable_shared(self) -> list[ResolvedMsg]: ...
    @property
    def unresolvables(self) -> list[UnResolvable]: ...
    @property
    def fixed_issues(self) -> list[ResolvedMsg]: ...

def fix_requirements_lock(
    loader: VenvMapLoader,
    venv_relpath: str,
    is_dry_run: Any | None = False,
) -> tuple[
    list[ResolvedMsg],
    list[UnResolvable],
    list[tuple[str, Resolvable, Pin | PinDatum]],
]: ...
