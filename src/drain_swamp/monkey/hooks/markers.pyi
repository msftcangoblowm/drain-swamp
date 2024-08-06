from collections.abc import Callable
from typing import (
    TypeVar,
    overload,
)

_F = TypeVar("_F", bound=Callable[..., object])

# From types-pluggy
class HookimplMarker:
    project_name: str
    def __init__(self, project_name: str) -> None: ...
    @overload
    def __call__(
        self,
        function: _F,
        hookwrapper: bool = False,
        optionalhook: bool = False,
        tryfirst: bool = False,
        trylast: bool = False,
        specname: str | None = None,
        wrapper: bool = False,
    ) -> _F: ...
    @overload
    def __call__(
        self,
        function: None = None,
        hookwrapper: bool = False,
        optionalhook: bool = False,
        tryfirst: bool = False,
        trylast: bool = False,
        specname: str | None = None,
        wrapper: bool = False,
    ) -> Callable[[_F], _F]: ...

hook_impl: HookimplMarker  # noqa: E305
