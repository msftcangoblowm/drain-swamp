"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Utility function to retrieve the global hook_manager singleton.

.. py:data:: _PLUGIN_HOOKS
   :type: str
   :value: "drain_swamp.hooks"

   Entrypoint to load hooks from for built-in or installed plugins

.. py:data:: logger
   :type: logging.Logger

   Module level logger

.. seealso::

   kedro manager
   `[SOURCE] <https://raw.githubusercontent.com/kedro-org/kedro/main/kedro/framework/hooks/manager.py>`_
   `[LICENSE:Apache 2.0] <https://github.com/kedro-org/kedro/blob/main/LICENSE.md>`_

"""

import importlib.util
import inspect
import logging
import pkgutil
import sys
from collections.abc import Sequence
from types import ModuleType
from typing import TYPE_CHECKING

from pluggy import PluginManager

from .constants import (
    _PLUGIN_HOOKS,
    DOTTED_PATH_SPECS,
    HOOK_NAMESPACE,
)

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec

logger = logging.getLogger(__name__)

__all__ = (
    "before",
    "after",
    "get_plugin_manager",
)


def before(hook_name, hook_impls, kwargs):  # pragma: no cover
    """Hook call tracing. Before a hook is called

    :param hook_name: Name of hook implementation
    :type hook_name: str
    :param hook_impls:

       Sequence of HookImpl instances. Can see which hooks are being executed

    :type hook_impls: collections.abc.Sequence[pluggy.HookImpl]
    :param kwargs: Keyword args passed into hook impl instances
    :type kwargs: collections.abc.Mapping[str, typing.Any]

    Usage

    .. code-block:: text

       from pluggy import PluginManager
       namespace = "ds"
       pm = PluginManager(namespace)
       # add hookspecs
       # register hooks
       undo = pm.add_hookcall_monitoring(before, after)

    .. seealso::

       `hookcall monitoring <https://pluggy.readthedocs.io/en/latest/api_reference.html#pluggy.PluginManager.add_hookcall_monitoring>`_


    """
    msg_info = f"trace {hook_name} (before) {hook_impls!r} kwargs {kwargs!r}"
    logger.info(msg_info)


def after(outcome, hook_name, hook_impls, kwargs):  # pragma: no cover
    """Runs after plugin hook execution. Gatherings non-None outcomes into a list

    :param outcome: List of non-None plugin hook results
    :type outcome: pluggy.Result[typing.Any]
    :param hook_name: Name of hook implementation
    :type hook_name: str
    :param hook_impls:

       Sequence of HookImpl instances. Can see which hooks are being executed

    :type hook_impls: collections.abc.Sequence[pluggy.HookImpl]
    :param kwargs: Keyword args passed into hook impl instances
    :type kwargs: collections.abc.Mapping[str, typing.Any]
    """
    msg_info = (
        f"trace {hook_name} (after) {hook_impls!r} kwargs {kwargs!r} "
        f"--> {outcome.get_result()}"
    )
    logger.info(msg_info)


def lazy_dotted_path(dotted_path):
    """Dotted path useful for loading plugin specs

    Should not contain spec classes

    :param dotted_path: Dotted path to module
    :type dotted_path: str
    :returns: Lazy imported module
    :rtype: types.ModuleType
    :raises:

       - :py:exc:`TypeError` -- Expecting valid dotted path
       - :py:exc:`ValueError` -- No such module exists

    """
    mod_path = "drain_swamp.monkey.hooks:lazy_dotted_path"
    is_ng = dotted_path is None or not isinstance(dotted_path, str)
    if is_ng:
        msg_warn = (
            f"{mod_path} Expecting valid dotted path to module "
            "containing plugin functions"
        )
        raise TypeError(msg_warn)

    try:
        mod = sys.modules[dotted_path]
    except KeyError:
        mod = None

    if mod is None:
        try:
            spec = importlib.util.find_spec(dotted_path)
            module = importlib.util.module_from_spec(spec)
            loader = importlib.util.LazyLoader(spec.loader)
            # Make module with proper locking and get it inserted into sys.modules.
            loader.exec_module(module)
            mod = module
        except ModuleNotFoundError as exc:
            msg_warn = f"{mod_path} dotted path to nonexistant module {dotted_path}"
            raise ValueError(msg_warn) from exc
    else:  # pragma: no cover
        pass

    return mod


def lazy_package(mod_pkg):
    """Lazy load module

    - fullname is a dotted path

    module should contain only spec functions

    - fullname is a Sequence[ModuleType]

    modules should contain only spec classes module should have a
    ``__all__`` containing only the spec classes names

    :param mod_pkg: Dotted path to package module
    :type mod_pkg: ModuleType
    :returns: Lazy imported module
    :rtype: Sequence[types.ModuleType]
    :raises:

       - :py:exc:`TypeError` -- Unsupported type. Expecting dotted path or ModuleType

    """
    if TYPE_CHECKING:
        mod_path: str
        msg_warn: str
        plugins_dir_paths: Sequence[str]
        mod_specs: list[ModuleSpec]
        module: ModuleType

    mod_path = "drain_swamp.monkey.hooks.manager:lazy_package"
    is_not_module = mod_pkg is None or not inspect.ismodule(mod_pkg)
    if is_not_module:
        msg_warn = f"{mod_path} Expected package module got {type(mod_pkg)}"
        raise TypeError(msg_warn)

    # Should contain only spec classes, no spec functions
    package_plugins = mod_pkg
    """package_plugins package (folder tree) contains builtin plugins' implementations
    location of hook implementations: ..plugins/ds_*
    plugin package ``__init__.py`` is empty, so importing can't raise Exceptions
    onerror param is therefore unneeded
    """
    # Could contain package and sub package paths
    plugins_dir_paths = package_plugins.__path__

    # https://docs.python.org/3/library/importlib.html#importlib.machinery.ModuleSpec
    mod_specs = [
        module_finder.find_spec(name)
        for module_finder, name, _ in pkgutil.walk_packages(plugins_dir_paths)
    ]

    ret = []
    for spec in mod_specs:
        module = importlib.util.module_from_spec(spec)
        loader = importlib.util.LazyLoader(spec.loader)
        # Make module with proper locking and get it inserted into sys.modules.
        loader.exec_module(module)
        mod = module
        ret.append(mod)

    return ret


def _filter_specs(member):  # pragma: no cover
    """Filter function used by inspect. Filter out non-plugins

    :param member: A module member
    :type member: typing.Any
    :returns: True if a module member a class and is a registered
    :rtype: bool
    """
    ret = inspect.isfunction(member) or inspect.isclass(member)
    return ret


def iter_specs(mod, filter_=_filter_specs):  # pragma: no cover
    """Iteratable of pluggy spec or impl classes

    Too hard to inspect spec and impl classes and functions. Using spec
    module ``__all__`` in leiu of inspection or validator.

    :param mod: A package module
    :type mod: types.ModuleType
    :param filter_: A filter function which allows only classes
    :type filter_: collections.abc.Callable[[tying.Any], bool]
    :returns: Plugin classes Iterator
    :rtype: collections.abc.Iterable[typing.Any]
    """
    lst_members = inspect.getmembers(mod, _filter_specs)
    for name, member in lst_members:
        if name in mod.__all__:
            logger.info(f"member (yield): {member!r}")
            yield member
    yield from ()


def _create_hook_manager(namespace, specs_dotted_path):
    """Create a new PluginManager instance and register hook specs.

    :param namespace: hook namespace, so as to support multiple
    :type namespace: str
    :param specs_dotted_path: specs module dotted path
    :type specs_dotted_path: str
    :returns: Plugin manager instance
    :rtype: pluggy.PluginManager
    :meta private:

    .. todo:: lazy import

       Built-in specs are hardcoded. Refactor as lazy imports

    """
    manager = PluginManager(namespace)
    # manager.trace.root.setwriter(logger.debug)
    # undo = manager.enable_tracing()

    # Avoid TypeError
    assert isinstance(specs_dotted_path, str)

    # Load specs given dotted path to spec module
    mod_spec = lazy_dotted_path(specs_dotted_path)

    if isinstance(mod_spec, ModuleType):
        # DOTTED_PATH_SPECS was str, so mod_spec is ModuleType
        manager.add_hookspecs(mod_spec)
    elif isinstance(mod_spec, Sequence):  # pragma: no cover
        # DOTTED_PATH_SPECS was Sequence[ModuleType] --> Sequence[type]
        for kls in iter_specs(mod_spec):
            # types.ModuleType | type
            manager.add_hookspecs(kls)
    else:  # pragma: no cover
        pass

    return manager


def _register_hooks(pm, hooks):
    """Register all hooks as specified in ``hooks`` with the global ``hook_manager``.

    :param hook_manager: Hook manager instance to register the hooks with.
    :type hook_manager: pluggy.PluginManager
    :param hooks: Hooks that need to be registered.
    :type hooks: collections.abc.Iterable[typing.Any | tuple[typing.Any, str | None]]
    :meta private:
    """
    for hooks_collection in hooks:
        # Sometimes users might call hook registration more than once, in which
        # case hooks have already been registered, so we perform a simple check
        # here to avoid an error being raised and break user's workflow.
        if not isinstance(hooks_collection, tuple):
            plugin = hooks_collection
        else:  # pragma: no cover
            # Can pass in a (plugin, plugin name). Not sure what the point is
            plugin = hooks_collection[0]

        # Avoids ValueError
        is_registered = pm.is_registered(plugin)

        if inspect.ismodule(plugin) or inspect.isaclass(plugin):
            # module containing only functions
            # class implementing spec functions as class methods
            if not is_registered:
                pm.register(plugin)
            else:  # pragma: no cover
                pass
        else:  # pragma: no cover
            pass


def _register_hooks_entry_points(hook_manager, entrypoint_plugins, disabled_plugins):
    """Register pluggy hooks from python package entrypoints.

    :param hook_manager:

       Hook manager instance to register the hooks with.

    :type hook_manager: pluggy.PluginManager
    :param entrypoint_plugins:

       Setuptools entrypoint section to specify additional
       :code:`python -m build` time plugins

    :type entrypoint_plugins: str
    :param disabled_plugins:

       An iterable returning the names of plugins which hooks must not
       be registered; any already registered hooks will be unregistered.

    :type disabled_plugins: collections.abc.Iterable[str]
    :meta private:
    """
    already_registered = hook_manager.get_plugins()
    # Method name is misleading:
    # entry points are standard and don't require setuptools,
    # see https://packaging.python.org/en/latest/specifications/entry-points/
    hook_manager.load_setuptools_entrypoints(entrypoint_plugins)
    disabled_plugins = set(disabled_plugins)

    # Get list of plugin/distinfo tuples for all registered plugins.
    plugininfo = hook_manager.list_plugin_distinfo()
    plugin_names = set()
    disabled_plugin_names = set()
    for plugin, dist in plugininfo:
        if dist.project_name in disabled_plugins:
            # `unregister()` is used instead of `set_blocked()` because
            # we want to disable hooks for specific plugin based on project
            # name and not `entry_point` name. Also, we log project names with
            # version for which hooks were registered.
            hook_manager.unregister(plugin=plugin)
            disabled_plugin_names.add(f"{dist.project_name}-{dist.version}")
        elif plugin not in already_registered:
            plugin_names.add(f"{dist.project_name}-{dist.version}")
        else:  # pragma: no cover
            pass

    if len(disabled_plugin_names) != 0:  # pragma: no cover
        str_disabled_plugins = ", ".join(sorted(disabled_plugin_names))
        msg_debug = (f"Hooks are disabled for plugin(s): {str_disabled_plugins}",)
        logger.debug(msg_debug)
    else:  # pragma: no cover
        pass

    if len(plugin_names) != 0:  # pragma: no cover
        str_plugin_names = ", ".join(sorted(plugin_names))
        str_plugin_count = len(plugin_names)
        msg_debug = (
            f"Registered hooks from {str_plugin_count} installed "
            f"plugin(s): {str_plugin_names}"
        )
        logger.debug(msg_debug)
    else:  # pragma: no cover
        pass


def get_plugin_manager(
    mod_pkg_plugins,
    namespace=HOOK_NAMESPACE,
    specs_dotted_path=DOTTED_PATH_SPECS,
    entrypoint_plugins=_PLUGIN_HOOKS,
):
    """Get plugin manager

    - set specs

    - load builtin hooks

    - load entrypoint hooks

    :param mod_pkg_plugins: plugins subpackage module
    :type mod_pkg_plugins: types.ModuleType
    :param namespace:

       Default HOOK_NAMESPACE. hook namespace, so as to support multiple

    :type namespace: str | None
    :param specs_dotted_path: Default DOTTED_PATH_SPECS. dotted path to specs module
    :type specs_dotted_path: str | None
    :param entrypoint_plugins:

       Default _PLUGIN_HOOKS. setuptools entrypoint section to specify
       additional :code:`python -m build` time plugins

    :type entrypoint_plugins: str | None
    :returns: Plugin manager instance
    :rtype: pluggy.PluginManager
    :raises:

      - :py:exc:TypeError -- Expected param mod_pkg_plugins to be a types.ModuleType
        Package folder with modules containg hook implementation functions

    """
    try:
        assert isinstance(mod_pkg_plugins, ModuleType)
    except AssertionError as e:
        msg_exc = (
            "Positional param expected package module. Package folder "
            "with modules containg hook implementation functions"
        )
        raise TypeError(msg_exc) from e

    is_namespace_ng = namespace is None or not isinstance(namespace, str)
    if is_namespace_ng:  # pragma: no cover
        namespace = HOOK_NAMESPACE
    else:  # pragma: no cover
        pass

    is_spec_dotted_path_ng = specs_dotted_path is None or not isinstance(
        specs_dotted_path, str
    )
    if is_spec_dotted_path_ng:  # pragma: no cover
        specs_dotted_path = DOTTED_PATH_SPECS
    else:  # pragma: no cover
        pass

    is_ep_plugins_ng = entrypoint_plugins is None or not isinstance(
        entrypoint_plugins, str
    )
    if is_ep_plugins_ng:  # pragma: no cover
        entrypoint_plugins = _PLUGIN_HOOKS
    else:  # pragma: no cover
        pass

    pm = _create_hook_manager(namespace, specs_dotted_path)

    """package_plugins package (folder tree) contains builtin plugins' implementations
    location of hook implementations: ..plugins/ds_*
    plugin package ``__init__.py`` is empty, so importing can't raise Exceptions
    onerror param is therefore unneeded
    """
    mods = lazy_package(mod_pkg_plugins)
    _register_hooks(pm, mods)

    # dump support for plugin impl klasses
    """
    impls = []
    for mod in mods:
        # plugin impl module
        impls.append(mod)

        for kls in iter_specs(mod):
            log.info(f"{mod_path} plugin name: {kls.__name__!r}")
            # Format for plugins: "{namespace}-{kls.__name__}"
            impls.append((kls(), f"{namespace}-{kls.__name__}"))
        pass
    log.info(f"{mod_path} impls (built-in): {impls!r}")
    _register_hooks(pm, impls)
    """
    pass

    """Occurring during :code:`python -m build`, only way to
    specify more plugins is using entrypoints
    """
    iter_disabled_plugins = ()
    _register_hooks_entry_points(pm, entrypoint_plugins, iter_disabled_plugins)

    return pm
