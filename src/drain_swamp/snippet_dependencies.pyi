import logging
from collections.abc import (
    Generator,
    Iterator,
    Sequence,
)
from pathlib import Path

__all__ = ("SnippetDependencies",)

_logger: logging.Logger

def _fix_suffix(suffix: str) -> str: ...
def _check_are_requirements_files(in_files: Sequence[Path]) -> None: ...

class SnippetDependencies:
    def _compose_dependencies_line(self, suffix: str) -> Iterator[str]: ...
    def _compose_optional_lines(self, suffix: str) -> Iterator[str]: ...
    def __call__(
        self,
        suffix: str,
        parent_dir: Path,
        gen_in_files: Generator[Path, None, None],
        required: tuple[str, Path] | None,
        optionals: dict[str, Path],
    ) -> str: ...
