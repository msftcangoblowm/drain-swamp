from pathlib import Path

__all__ = (
    "dump_version",
    "write_version_to_path",
    "write_version_files",
)

TEMPLATES: dict[str, str]

def dump_version(
    root: Path,
    version: str,
    write_to: Path,
    template: str | None = None,
) -> None: ...
def _validate_template(
    target: Path,
    template: str | None,
) -> str: ...
def write_version_to_path(
    target: Path,
    template: str | None,
    version: str,
) -> None: ...
def write_version_files(
    version: str,
    root: Path,
    write_to: str | None,
    version_file: str | None,
    is_only_not_exists: bool | None = False,
) -> None: ...
