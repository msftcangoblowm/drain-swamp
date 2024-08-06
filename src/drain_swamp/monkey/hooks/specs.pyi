from collections.abc import Callable
from typing import (
    Any,
    TypeVar,
    overload,
)

_F = TypeVar("_F", bound=Callable[..., object])

# From types-pluggy
class HookspecMarker:
    project_name: str
    def __init__(self, project_name: str) -> None: ...
    @overload
    def __call__(
        self,
        function: _F,
        firstresult: bool = False,
        historic: bool = False,
        warn_on_impl: Warning | None = None,
    ) -> _F: ...
    @overload
    def __call__(
        self,
        function: None = None,
        firstresult: bool = False,
        historic: bool = False,
        warn_on_impl: Warning | None = None,
    ) -> Callable[[_F], _F]: ...

hook_spec: HookspecMarker  # noqa: E305

@hook_spec
def ds_before_version_infer(config_settings: dict[str, Any]) -> str | None: ...
@hook_spec
def ds_on_version_infer(config_settings: dict[str, Any]) -> str | None: ...
@hook_spec
def ds_after_version_infer(config_settings: dict[str, Any]) -> str | None: ...
