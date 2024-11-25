import abc
from pathlib import Path

from .lock_datum import (
    DATUM,
    Pin,
    PinDatum,
)
from .lock_filepins import FilePins
from .pep518_venvs import VenvMapLoader

__all__ = (
    "LoaderImplementation",
    "LoaderPin",
    "LoaderPinDatum",
    "from_loader_filepins",
)

def _from_loader_pins(
    loader: VenvMapLoader,
    venv_path: str | Path,
    suffix: str = ...,
    filter_by_pin: bool | None = True,
) -> set[Pin]: ...
def from_loader_filepins(
    loader: VenvMapLoader,
    venv_path: str | Path,
    suffix_last: str = ...,
) -> list[FilePins]: ...
def _from_loader_pindatum(
    loader: VenvMapLoader,
    venv_path: str | Path,
    suffix: str = ...,
    filter_by_pin: bool | None = True,
) -> set[PinDatum]: ...

class LoaderImplementation(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        loader: VenvMapLoader,
        venv_path: str | Path,
        suffix: str = ...,
        filter_by_pin: bool | None = True,
    ) -> set[DATUM]: ...

class LoaderPin(LoaderImplementation):
    def __call__(
        self,
        loader: VenvMapLoader,
        venv_path: str | Path,
        suffix: str = ...,
        filter_by_pin: bool | None = True,
    ) -> set[DATUM]: ...

class LoaderPinDatum(LoaderImplementation):
    def __call__(
        self,
        loader: VenvMapLoader,
        venv_path: str | Path,
        suffix: str = ...,
        filter_by_pin: bool | None = True,
    ) -> set[DATUM]: ...
