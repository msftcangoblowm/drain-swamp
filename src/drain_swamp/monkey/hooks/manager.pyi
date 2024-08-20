import logging
from collections.abc import (
    Callable,
    Iterable,
    Mapping,
    Sequence,
)
from types import ModuleType
from typing import Any

from pluggy import (
    HookImpl,
    PluginManager,
    Result,
)

logger: logging.Logger

__all__ = (
    "before",
    "after",
    "get_plugin_manager",
)

def before(
    hook_name: str,
    hook_impls: Sequence[HookImpl],
    kwargs: Mapping[str, Any],
) -> None: ...
def after(
    outcome: Result[Any],
    hook_name: str,
    hook_impls: Sequence[HookImpl],
    kwargs: Mapping[str, Any],
) -> None: ...
def lazy_dotted_path(dotted_path: str) -> ModuleType: ...
def lazy_package(
    mod_pkg: ModuleType,
) -> Sequence[ModuleType]: ...
def _filter_specs(member: Any) -> bool: ...
def iter_specs(
    mod: ModuleType,
    filter_: Callable[[Any], bool] = ...,
) -> Iterable[Any]: ...
def _create_hook_manager(namespace: str, specs_dotted_path: str) -> PluginManager: ...
def _register_hooks(
    hook_manager: PluginManager,
    hooks: Iterable[Any | tuple[Any, str | None]],
) -> None: ...
def _register_hooks_entry_points(
    hook_manager: PluginManager,
    entrypoint_plugins: str,
    disabled_plugins: Iterable[str],
) -> None: ...
def get_plugin_manager(
    mod_pkg_plugins: ModuleType,
    namespace: str | None = ...,
    specs_dotted_path: str | None = ...,
    entrypoint_plugins: str | None = ...,
) -> PluginManager: ...
