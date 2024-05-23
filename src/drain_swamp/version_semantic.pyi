import types
from pathlib import Path
from typing import Any

__all__ = (
    "SemVersion",
    "SetuptoolsSCMNoTaggedVersionError",
    "sanitize_tag",
    "get_version",
)

_map_release: types.MappingProxyType[str, str]

class SetuptoolsSCMNoTaggedVersionError(AssertionError):
    def __init__(self, msg: str) -> None: ...

def path_or_cwd(val: Any | None) -> Path: ...
def _scm_key(prog_name: str) -> str: ...
def _current_tag(path: Path | None = None) -> str | None: ...
def _strip_epoch(ver: str) -> tuple[str | None, str]: ...
def _strip_local(ver: str) -> tuple[str | None, str]: ...
def _remove_v(ver: str) -> str: ...
def sanitize_tag(ver: str) -> str: ...
def get_version(
    ver: str,
    is_use_final: bool = False,
) -> tuple[tuple[int, int, int, str, int], int | None]: ...
def _current_version(path: Path | None = None) -> str | None: ...
def _tag_version(
    next_version: str | None = "",
    path: Path | None = None,
    package_name: str | None = None,
) -> str | None: ...
def _arbritary_version(
    next_version: str,
    path: Path | None = None,
    package_name: str | None = None,
) -> str | None: ...
def _get_app_name(path: Path | None = None) -> str | None: ...

class SemVersion:
    CURRENT_ALIAS_DEFAULT: str = "current"
    CURRENT_ALIASES: tuple[str, str] = ...
    KINDS: tuple[str, str, str] = ...

    def __init__(
        self,
        path: Path | None = None,
        is_use_final: Any | None = False,
    ) -> None: ...
    @classmethod
    def sanitize_kind(cls, kind: str | None = None) -> str: ...
    @property
    def path_cwd(self) -> Path: ...
    @path_cwd.setter
    def path_cwd(self, val: Any) -> None: ...
    @property
    def is_use_final(self) -> bool: ...
    @is_use_final.setter
    def is_use_final(self, val: Any) -> None: ...
    @property
    def major(self) -> int | None: ...
    @property
    def minor(self) -> int | None: ...
    @property
    def micro(self) -> int | None: ...
    @property
    def releaselevel(self) -> str | None: ...
    @releaselevel.setter
    def releaselevel(self, val: str) -> None: ...
    @property
    def releaselevel_abbr(self) -> str: ...
    @property
    def serial(self) -> int | None: ...
    @property
    def dev(self) -> int | None: ...
    def parse_ver(self, ver: str) -> None: ...
    def version_xyz(self) -> str | None: ...
    def anchor(self) -> str | None: ...
    def readthedocs_url(
        self,
        package_name: str,
        is_latest: bool | None = False,
    ) -> str: ...
    def version_clean(
        self, kind: str, package_name: str | None = None
    ) -> str | None: ...
    @property
    def __version__(self) -> str | None: ...
