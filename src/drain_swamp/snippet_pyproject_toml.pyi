from pathlib import Path
from typing import Final

from .snip import ReplaceResult

SNIPPET_NO_MATCH: Final[str]  # noqa: F401
SNIPPET_VALIDATE_FAIL: Final[str]  # noqa: F401

__all__ = (
    "SNIPPET_VALIDATE_FAIL",
    "SNIPPET_NO_MATCH",
    "snippet_replace_suffixes",
)

def snippet_replace_suffixes(
    path_config: Path,
    snippet_co: str | None = None,
) -> ReplaceResult | None: ...
