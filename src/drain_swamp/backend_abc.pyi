import abc
import logging
import sys
from collections.abc import (
    Generator,
    Iterator,
)
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Final,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

__all__ = ("BackendType",)
_logger: Final[logging.Logger]
is_module_debug: Final[bool]
entrypoint_name: Final[str]

def try_dict_update(
    set_both: dict[str, Path],
    path_config: Path,
    target_x: str,
    path_relative_x: Path,
    is_bypass: Any | None = False,
) -> None: ...
def get_optionals_cli(
    d_both: dict[str, Path],
    path_config: Path,
    optionals: dict[str, Any],
) -> None: ...
def get_optionals_pyproject_toml(
    d_both: dict[str, Path],
    d_pyproject_toml: dict[str, Any],
    path_config: Path,
    is_bypass: bool | None = False,
) -> None: ...
def get_required_pyproject_toml(
    d_pyproject_toml: dict[str, Any],
    path_config: Path,
    is_bypass: bool | None = False,
) -> tuple[str, Path] | None: ...
def get_required_cli(
    path_config: Path,
    required: tuple[str, Any] | None = None,
    is_bypass: bool | None = False,
) -> tuple[str, Path] | None: ...
def folders_implied_init(
    parent_dir: Path,
    optionals: dict[str, Path],
    required: tuple[str, Path] | None = None,
) -> set[Path]: ...
def get_additional_folders_pyproject_toml(
    d_pyproject_toml: dict[str, Any],
    path_config: Path,
    implied_folders: set[Path],
    is_bypass: bool | None = False,
) -> set[Path]: ...
def folders_additional_cli(
    parent_dir: Path,
    folders_implied: set[Path],
    additional_folders: tuple[Path] = ...,
) -> set[Path]: ...
def ensure_folder(val: Any) -> Path: ...

class BackendType(abc.ABC):
    _path_required: tuple[str, Path] | None
    _paths_optional: dict[str, Path]
    _path_config: Path
    _parent_dir: Path
    _folders_implied: set[Path]
    _folders_additional: set[Path]
    BACKEND_NAME: ClassVar[str]
    PYPROJECT_TOML_SECTION_NAME: ClassVar[str]

    def __init__(
        self,
        path_config: Path,
        required: tuple[str, Path] | None = None,
        optionals: dict[str, Path] = {},
        parent_dir: Path | None = None,
        additional_folders: tuple[Path, ...] = (),
    ) -> None: ...
    def load(
        self,
        d_pyproject_toml: dict[str, Any],
        required: tuple[str, Path] | None = None,
        optionals: dict[str, Path] = {},
        parent_dir: Path | None = None,
        additional_folders: tuple[Path, ...] = (),
    ) -> None: ...
    @staticmethod
    def determine_backend(d_pyproject_toml: dict[str, Any]) -> str: ...
    @staticmethod
    def get_required(
        d_pyproject_toml: dict[str, Any],
        path_config: Path,
        required: tuple[str, Any] | None = None,
    ) -> tuple[str, Path] | None: ...
    @staticmethod
    def get_optionals(
        d_pyproject_toml: dict[str, Any],
        path_config: Path,
        optionals: dict[str, Any],
    ) -> dict[str, Path]: ...
    @property
    @abc.abstractmethod
    def backend(self) -> str: ...
    @property
    def path_config(self) -> Path: ...
    @property
    def parent_dir(self) -> Path: ...
    @parent_dir.setter
    def parent_dir(
        self,
        parent_dir: Path | None = None,
    ) -> None: ...
    @property
    def required(self) -> tuple[str, Path] | None: ...
    @property
    def optionals(self) -> dict[str, Path]: ...
    @property
    def folders_implied(self) -> set[Path]: ...
    @property
    def folders_additional(self) -> set[Path]: ...
    @classmethod
    def __subclasshook__(cls, C: Any) -> bool: ...
    @classmethod
    def get_registered(cls) -> Iterator[type[Self]]: ...
    def in_files(self) -> Generator[Path, None, None]: ...
    @staticmethod
    def is_locked(
        path_config: Path,
    ) -> bool: ...
