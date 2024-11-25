import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .lock_datum import (
    DatumByPkg,
    Pin,
    PinDatum,
)

if sys.version_info >= (3, 10):  # pragma: no cover py-gte-310-else
    from typing import TypeAlias
else:  # pragma: no cover py-gte-310
    from typing_extensions import TypeAlias

__all__ = (
    "PkgsWithIssues",
    "Resolvable",
    "ResolvedMsg",
    "UnResolvable",
    "has_discrepancies_version",
    "tunnel_blindness_suffer_chooses",
    "write_to_file_nudge_pin",
)

DC_SLOTS: dict[str, bool]
is_module_debug: Final[bool]
_logger: Final[logging.Logger]

PkgsWithIssues: TypeAlias = dict[str, dict[str, Version | set[Version]]]

def has_discrepancies_version(d_by_pkg: DatumByPkg) -> PkgsWithIssues: ...
def _get_ss_set(set_pindatum: set[Pin | PinDatum]) -> set[SpecifierSet]: ...
def tunnel_blindness_suffer_chooses(
    set_pindatum: set[Pin | PinDatum],
    highest: Version,
    others: set[Version],
) -> tuple[set[SpecifierSet], str, bool]: ...
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
    pins: set[Pin] | set[PinDatum]

    def pprint_pins(self) -> str: ...

@dataclass(**DC_SLOTS)
class ResolvedMsg:
    abspath_f: Path
    nudge_pin_line: str

def extract_full_package_name(
    line: str,
    pkg_name_desired: str,
) -> str | None: ...
def write_to_file_nudge_pin(
    path_f: Path,
    pkg_name: str,
    nudge_pin_line: str,
) -> None: ...
