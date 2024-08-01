import re
from collections.abc import Sequence
from enum import (
    Enum,
    auto,
)
from pathlib import Path
from typing import (
    Any,
    ClassVar,
)

__all__ = (
    "Snip",
    "ReplaceResult",
)

class ReplaceResult(Enum):
    VALIDATE_FAIL = auto()
    NO_MATCH = auto()
    REPLACED = auto()
    NO_CHANGE = auto()
    def __eq__(self, other: object) -> bool: ...

def check_matching_tag_count(
    contents: str,
    token_start: str | None = None,
    token_end: str | None = None,
) -> bool: ...
def check_not_nested_or_out_of_order(
    contents: str,
    token_start: str | None = None,
    token_end: str | None = None,
) -> bool: ...
def sanitize_id(id_: Any | None = "") -> str: ...

class Snip:
    TOKEN_START: ClassVar[str]
    TOKEN_END: ClassVar[str]
    PATTERN_W_ID: re.Pattern[str]

    def __init__(
        self,
        fname: str | Path,
        is_quiet: bool | None = False,
    ) -> None: ...
    @property
    def path_file(self) -> Path: ...
    @path_file.setter
    def path_file(self, val: Any) -> None: ...
    def is_file_ok(self) -> bool: ...
    @property
    def is_quiet(self) -> bool: ...
    @is_quiet.setter
    def is_quiet(self, val: Any) -> None: ...
    @property
    def is_infer(self) -> bool: ...
    @property
    def snippets(self) -> Sequence[tuple[str, str]] | ReplaceResult: ...
    def print(self) -> Sequence[tuple[str, str]] | ReplaceResult: ...
    def get_file(self) -> str: ...
    def validate(self) -> bool: ...
    def contents(self, id_: str | None = None) -> str | ReplaceResult: ...
    def replace(self, replacement: str, id_: str | None = "") -> ReplaceResult: ...
