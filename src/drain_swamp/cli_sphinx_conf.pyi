import logging
from pathlib import Path
from typing import Final

_logger: Final[logging.Logger]
entrypoint_name: Final[str]

help_path: Final[str]
help_kind: Final[str]
help_copyright_year: Final[str]
help_snippet_co: Final[str]
EPILOG: Final[str]

def main() -> None: ...
def sphinx_conf_snip(
    path: Path | None = ...,
    kind: str | None = "current",
    copyright_start_year: int | None = 1970,
    snippet_co: str | None = None,
) -> None: ...
