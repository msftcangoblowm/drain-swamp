from pathlib import Path
from typing import Final

entrypoint_name: Final[str]
help_path: Final[str]
help_is_write: Final[str]
help_write_to: Final[str]
EPILOG_SCM_VERSION_GET: Final[str]
EPILOG_SCM_VERSION_WRITE: Final[str]

def main() -> None: ...
def get_scm_version(path: Path, is_write: bool, write_to: str | None) -> None: ...
def write_scm_version(scm_ver: str, path: Path, write_to: str | None) -> None: ...
