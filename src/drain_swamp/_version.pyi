from typing import Final

__all__ = [
    "__version__",
    "__version_tuple__",
    "version",
    "version_tuple",
    "__commit_id__",
    "commit_id",
]

version: Final[str]
__version__: Final[str]
__version_tuple__: Final[tuple[int | str, ...]]
version_tuple: Final[tuple[int | str, ...]]
commit_id: str | None
__commit_id__: str | None
