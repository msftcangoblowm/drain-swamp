from collections.abc import (
    Generator,
    Iterator,
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

from typing_extensions import Self

from .monkey.pyproject_reading import TOML_RESULT

DC_SLOTS: dict[str, bool]
TOML_SECTION_VENVS: Final[str]
DICT_SEARCH_KEY: Final[str]

@dataclass(**DC_SLOTS)
class VenvReq:
    project_base: Path
    venv_relpath: str
    req_relpath: str
    req_folders: tuple[str]

    @property
    def venv_abspath(self) -> Path: ...
    @property
    def req_abspath(self) -> Path: ...
    @property
    def is_req_shared(self) -> bool: ...
    def _req_folders_abspath(self) -> Generator[Path, None, None]: ...
    def reqs_all(self, suffix: str = ...) -> Generator[Path, None, None]: ...

@dataclass(**DC_SLOTS)
class VenvMapLoader:
    pyproject_toml_base_path: InitVar[str]
    project_base: Path = ...
    pyproject_toml: Path = ...
    l_data: Sequence[TOML_RESULT] = ...

    def __post_init__(
        self,
        pyproject_toml_base_path: str,
    ) -> None: ...
    @staticmethod
    def load_data(
        pyproject_toml_base_path: str,
    ) -> tuple[Sequence[TOML_RESULT], Path, Path]: ...
    def parse_data(self) -> tuple[list[VenvReq], list[str]]: ...
    def ensure_abspath(self, key: str | Path) -> Path: ...

class VenvMap(Iterator[VenvReq]):
    _loader: VenvMapLoader
    _iter: Iterator[VenvReq]
    _venvs: list[VenvReq]
    _missing: list[str]

    __slots__ = ("_loader", "_venvs", "_iter", "_missing")

    def __init__(self, loader: VenvMapLoader) -> None: ...
    @property
    def missing(self) -> list[str]: ...
    @property
    def project_base(self) -> Path: ...
    def ensure_abspath(self, key: str | Path) -> Path: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> VenvReq: ...
    def __contains__(self, key: Any) -> bool: ...
    def __getitem__(self, key: int | slice) -> list[VenvReq] | VenvReq: ...
    def reqs(self, key: Any) -> list[VenvReq]: ...
