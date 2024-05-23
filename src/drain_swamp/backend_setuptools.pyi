from collections.abc import (
    Iterator,
    Sequence,
)
from pathlib import Path
from typing import (
    Any,
    ClassVar,
)

from .backend_abc import BackendType

__all__ = ("BackendSetupTools",)

class BackendSetupTools(BackendType):
    _backend: str
    _extras: tuple[str, ...]
    _path_required: tuple[str, Path] | None
    _paths_optional: dict[str, Path]

    BACKEND_NAME: ClassVar[str] = "setuptools"
    PYPROJECT_TOML_SECTION_NAME: ClassVar[str] = "tool.setuptools.dynamic"
    __slots__ = ("path_config", "_extras", "_path_required", "_paths_optional")

    def __init__(
        self,
        d_pyproject_toml: dict[str, Any],
        path_config: Path,
        required: Path | None = None,
        optionals: Sequence[Path] = (),
        extras: Sequence[str] = (),
        parent_dir: Path | None = None,
    ) -> None: ...
    @property
    def backend(self) -> str: ...
    def compose_dependencies_line(self, suffix: str) -> Iterator[str]: ...
    def compose_optional_lines(self, suffix: str) -> Iterator[str]: ...
    def compose(self, suffix: str) -> str: ...
