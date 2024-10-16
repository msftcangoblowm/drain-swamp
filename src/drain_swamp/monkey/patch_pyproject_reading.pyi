import abc
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import (
    Any,
    NamedTuple,
)

from setuptools_scm._integration.toml import TOML_RESULT

__all__ = (
    "ReadPyproject",
    "ReadPyprojectStrict",
)

log: logging.Logger

class PyProjectData(NamedTuple):
    path: Path
    tool_name: str
    project: TOML_RESULT
    section: TOML_RESULT | Sequence[TOML_RESULT]

    @property
    def project_name(self) -> str | None: ...

class ReadPyprojectBase(abc.ABC):
    @abc.abstractmethod
    def update(
        self,
        d_target: dict[str, Any],
        d_other: dict[str, Any],
        key_name: str | None = None,
        key_value: str | None = None,
    ) -> None: ...
    def __call__(
        self,
        path: Path = ...,
        tool_name: Sequence[str] | str = ...,
        require_section: bool = True,
        key_name: str | None = None,
        is_expect_list: bool = False,
    ) -> PyProjectData: ...

class ReadPyproject(ReadPyprojectBase):
    def update(
        self,
        d_target: dict[str, Any],
        d_other: dict[str, Any],
        key_name: str | None = None,
        key_value: str | None = None,
    ) -> None: ...

class ReadPyprojectStrict(ReadPyprojectBase):
    def update(
        self,
        d_target: dict[str, Any],
        d_other: dict[str, Any],
        key_name: str | None = None,
        key_value: str | None = None,
    ) -> None: ...

def read_pyproject(
    path: Path = ...,
    tool_name: Sequence[str] | str = ...,
    require_section: bool = True,
) -> PyProjectData: ...
