from pathlib import Path
from typing import Any

ENDINGS: tuple[str, str, str]
__all__ = (
    "is_shared",
    "replace_suffixes_last",
)

def is_shared(file_name: str) -> bool: ...
def replace_suffixes_last(
    abspath_f: Any,
    suffix_last: str,
) -> Path: ...
