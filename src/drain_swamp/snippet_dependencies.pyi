import logging
from collections.abc import (
    Iterator,
    Mapping,
    Sequence,
)
from pathlib import Path

from typing_extensions import TypeAlias

__all__ = (
    "SnippetDependencies",
    "get_required_and_optionals",
    "generate_snippet",
)
_logger: logging.Logger

T_REQUIRED: TypeAlias = tuple[str, Path] | None
T_OPTIONALS: TypeAlias = Mapping[str, Path]

def _fix_suffix(suffix: str) -> str: ...

class SnippetDependencies:
    def _compose_dependencies_line(self, suffix: str) -> Iterator[str]: ...
    def _compose_optional_lines(self, suffix: str) -> Iterator[str]: ...
    def __call__(
        self,
        suffix: str,
        parent_dir: Path,
        required: tuple[str, Path] | None,
        optionals: dict[str, Path],
    ) -> str: ...

def get_required_and_optionals(
    path_f: Path,
    tool_name: str | Sequence[str] = ...,
) -> tuple[Sequence[Path], T_REQUIRED, T_OPTIONALS]: ...
def generate_snippet(
    path_cwd: Path,
    path_config: Path,
    tool_name: str | Sequence[str] = ...,
    suffix_last: str = ...,
) -> str: ...
