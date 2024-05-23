import logging
from pathlib import Path
from typing import Final

_logger: logging.Logger
entrypoint_name: Final[str]
help_path: Final[str]
help_snippet_co: Final[str]
help_kind: Final[str]
EPILOG_SEED: Final[str]
EPILOG_EDITS: Final[str]

def main() -> None: ...
def seed(path: Path) -> None: ...
def edit(path_cwd: Path, kind: str, snippet_co: str | None = None) -> None: ...
